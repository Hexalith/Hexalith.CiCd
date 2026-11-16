---
title: '11 — Pilot migration: Commons and PolymorphicSerializations'
type: 'chore'
created: '2026-11-15'
status: 'in-progress'
baseline_commit: '37e73a99dfe82c3b7741554d6f4ff2207711644b'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/specs/spec-cicd/evidence/11/planning.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Both pilots still use legacy pipelines. Adoption must preserve product checks and establish real delivery, restricted-token behavior and nightly release evidence.

**Approach:** After stories 10-1/10-2 and AD-21 preconditions pass, prepare product changes, release shared publication verification, register/render both modules, and let App delivery adopt them. Accept only after the real-night pilot checkpoint.

## Boundaries & Constraints

**Always:** Follow AD-21 ordering and the gate rule. Use the protected module token for module product writes and probes; CiCd-agent for CiCd/Builds; command-local maintainer profile for authorized administration. Preserve SDK pins, all product tests and foreign instruction/settings content. Use disposable verification workspaces under `run-with-temp`; save evidence outside scratch.

**Never:** Directly edit module-owned-perimeter files, obtain the App key, initialize nested submodules, weaken checks or duplicate-scan policy, adopt another module, manufacture delivery/nightly evidence, or merge probe PRs. Only delivery/restore writes owned files. Remove legacy credentials only immediately after actual adoption.

**Human decisions, 2026-11-15:** This session owns 10-2 after 10-1 and then resumes story 11. Required provisioning is authorized through existing authenticated access; report concrete access failures separately from authorization.

**Deferred check:** The human accepted 10-1's three verified outcomes and cleanup as the prerequisite handoff. Create a restricted-token product-only probe branch/PR before real delivery; after delivery changes main's workflows, test that PR's Update branch and repeat fresh-main product branching. Keep 10-2's temporary prohibition until the actual result establishes its behavior. Record exact revisions, outcomes and cleanup before pilot acceptance.

## I/O & Edge-Case Matrix

| State | Expected behavior |
| --- | --- |
| Missing dependency, policy or credential | Stop before adoption; record the unmet prerequisite. |
| Disabled Dependabot response | Accept boolean `enabled: false` or authenticated legacy 404 after administrative preflight; reject enabled/malformed/error responses. |
| Package indexing delay or conflicting existing version | Bounded retry for transient absence; mismatched ID/version/source fails before GitHub publication. |
| Delivery race or failed module | Existing bounded forward-only delivery applies; retain per-module report and do not claim adoption. |
| No Builds update or releasable change overnight | Record authenticated no-bump/nothing-to-release outcome; do not force a release. |

</frozen-after-approval>

## Code Map

- `evidence/11/planning.md` under the main spec folder: exact revisions, preflight, API failure, gate assessment and command details; `preflight.json` and `dependabot-disabled-probe.log` substantiate it.
- `tools/deliver.py:app_checks`, `tools/tests/test_deliver.py`: disabled-response compatibility; preserve permission checks.
- Builds `Github/lib/release_publish.py`, `release_draft.py:package_identity`, `tests/test_release_publish.py`: authenticated package inventory, publisher and shared regression coverage.
- Commons `scripts/{pack-release-packages,validate-nuget-packages,validate-consumer-package-references}.py`: distinct product package/consumer checks.
- Both modules `tools/{verify_nuget_release,test_verify_nuget_release}.py`: duplicated post-publication checks to hoist, then retire.
- `tools/render.py`, `tools/check_global.py`, `tools/validate.py`, `docs/nightly.md`: reuse rendering, committed-candidate checks, live validation and observation.

## Tasks & Acceptance

**Execution:**

- [ ] `evidence/11/` — recheck completed predecessors and document AD-21 provisioning: App scope, stale release/tag assessment, exact main/v* rulesets, main-only release environment, module push identities, scoped NuGet policies, org grants and security/retention settings. Preserve existing publication access until adoption.
- [x] `tools/deliver.py`, `tools/tests/test_deliver.py` — handle the observed disabled response; test false/true/malformed/404/authorization-error cases and sibling isolation.
- [ ] `references/Hexalith.Builds/Github/lib/release_publish.py` and its tests — add generic bounded live NuGet verification before finalization, reusing authenticated inventory and package identity parsing; preserve missing/indexing-delay/source-conflict coverage. Release through the interactive shared pipeline and await an acceptable tag before adoption.
- [ ] Both module `tools/` and root `package.json`/lockfile — after shared coverage exists, retire duplicated legacy verification code/tests/manifests and tool-only npm files using the module token. Let delivery remove owned legacy configuration/workflows.
- [x] Commons `.github/actions/after-unit-tests/action.yml` and its three package scripts — retain payload/symbol and isolated-consumer checks without another module build/restore; fix consumer SDK/cache isolation and CI audit-off/package flags. Test real package consumption; preserve all C# suites.
- [ ] `builds-version`, `setup/Hexalith.{Commons,PolymorphicSerializations}.yml`, `rendered/`, direct gitlinks — pin released shared behavior, use each `.slnx`, enable Commons' hook and default C# analysis. Before adoption, create the disposable product-only probe branch/PR from current module main and record base/head. Render and validate one committed candidate before pushing; hooks must already exist on live main.
- [ ] `evidence/11/` — authenticate both delivery commits/refs/reports; immediately enable immutable releases and remove other NuGet policies and legacy secret/key/Zot access. Record green CI, the scheduled night and post-delivery branch/Update-branch outcomes; clean probes and confirm/correct 10-2 restrictions.

**Acceptance Criteria:**

- Given satisfied prerequisites, when delivery adopts the pilots, then both owned trees match accepted perimeters and product files/tests remain intact.
- Given missing or wrong-source published packages, when shared publication verifies the feed, then it cannot report successful GitHub publication.
- Given adopted main revisions, when restricted-token branch probes run, then actual server outcomes and complete cleanup are recorded without owned-file edits or probe merges.
- Given green pilot CI, when one real scheduled nightly finishes, then CodeQL, releases or valid no-release outcomes, scan, Builds bump/no-bump and delivery are evidenced before checkpoint acceptance.

## Implementation Notes

- The predecessor recheck confirms 10-1 and 10-2 are done; the approved deferred
  Update branch qualification and temporary prohibition remain intact.
  [Implementation readiness](../specs/spec-cicd/evidence/11/implementation-readiness.md)
  distinguishes completed local source work from outstanding provisioning,
  publication, adoption and live-night acceptance.
- Delivery accepts boolean `enabled: false` and authenticated legacy 404 after
  administrative preflight, while rejecting enabled/malformed/authorization
  responses with sibling isolation. The API rejects successful JSON `null` on
  absence-enabled reads, so it cannot be mistaken for 404 absence; other
  consumers retain their existing response-shape and identity diagnostics.
- Builds now verifies the authenticated inventory on the live NuGet feed
  between push and GitHub finalization, with bounded pending-package retry and
  reused ID/version/source parsing. Publisher regressions pass on Python 3.12
  and runner Python. No new shared release has been published, so the composite
  release task remains unchecked and legacy module copies are retained.
- Added Commons' package/consumer hook and CI packing flags; the isolated
  consumer uses its unchanged SDK pin and cleans its private NuGet caches.
  Both pilot package-mode builds, all 372 C# tests across nine suites, all twelve
  Commons payload/symbol package pairs and real isolated consumption passed.
  The existing payload/symbol validator and all C# tests remain intact.
- Initial local preparation performed no module adoption, owned-file edit,
  probe branch/PR, remote mutation or credential cleanup. Protected-token fetches refreshed the local
  module checkouts to current remote mains. Production setup/render and the
  Builds version pin remain unchanged.
- The initial provisioning attempt was blocked before its first step: the intended maintainer API
  cannot enumerate the App installation's selected repositories (HTTP 403), and
  the existing signed-in browser requires human **Confirm access** at the
  installation settings. Its selection remains unverified. No authentication
  bypass or access broadening was attempted; the browser stays on that prompt.
- Product-preparation pushes have a separate prerequisite failure:
  `python3 references/Hexalith.Builds/check.py` exits 2 in both pilot roots
  because the nested script is absent. Current shared local checking also
  requires the adopted configuration, which does not exist yet. The recorded
  package-mode results do not replace that mandated command. No nested
  submodule or owned-file bootstrap was created to bypass it; a pre-adoption
  check/bootstrap resolution remains necessary before the first module push.
- The first 2026-11-16 read-only refresh confirmed both blockers persisted. The intended
  maintainer API still returns HTTP 403 and the browser still requires human
  **Confirm access** at the exact App installation URL. Both required module
  checks again exit 2. Their legacy Builds pin
  `9f5d751f7ab0b7a621dcd18b589bf061fabac6ec` contains no checker, so nested
  initialization alone could not repair the gap. Current checking additionally
  requires adopted configuration and genuine delivered state. The concrete
  sequencing/verification decision is recorded in
  [pre-adoption check resolution](../specs/spec-cicd/evidence/11/pre-adoption-check-resolution.md);
  no frozen constraint was changed or exception assumed. No additional local
  source gap was found, and publication/adoption tasks remain incomplete.
- After the human completed GitHub **Confirm access**, saved App selection and
  verified it after browser reload: exactly Builds, CiCd and both pilots.
  Completed the authorized stale CodeQL/three orphan-tag cleanup, exact
  main/v* rulesets and main-only `hexalith-release` environments. Installed
  distinct scoped Zot identities and each environment's secret pair, preserving
  legacy access. Real authentication/foreign-write refusals and preservation
  checks pass. Full current details are in
  [provisioning status](../specs/spec-cicd/evidence/11/provisioning-status.md).
- Scoped NuGet policies remain incomplete: the first Commons submission
  returned a generic creation error, and refreshing exposed an expired NuGet
  session. Normal Microsoft sign-in now requires human face/fingerprint/PIN
  or security-key authentication. No new policy or specific duplicate/permission
  limitation is proved. Later settings/org-grant writes wait for this AD-21
  policy step. No module push, shared release, adoption, credential removal or
  pre-adoption-check substitution occurred; both human prerequisites remain
  separate from the already authorized provisioning.

## Spec Change Log

## Review Triage Log

## Verification

Completed logs under [evidence/11](../specs/spec-cicd/evidence/11/):

- `builds-publisher-python312.log` and `builds-publisher-python314.log`: 17
  publisher regressions passed on each interpreter, including actual composite
  rejection of missing, wrong-source and unauthorized feed responses.
- `package-mode-verification.py` and `package-mode-python314.log`: both builds,
  372 passing C# tests with zero skipped, twelve Commons payload/symbol package
  pairs and isolated consumer restore/build. Final Commons source hashes match
  the recorded successful overlays; disposable scratch was removed.
- `deliver-python312.log`: 20 delivery tests passed; the subsequent null guard
  receives a separate focused follow-up. `deliver-python314.log`: all 20 passed
  on runner Python 3.14.4 in 426.449 seconds, including the final null case.
- `deliver-null-python312.log`: all malformed/null/authorization sibling
  subcases passed in the focused Python 3.12 test. The initial broader runtime
  check exposed a diagnostic regression from globally rejecting null; its log
  is retained. The correction limits rejection to absence-enabled reads and
  gets direct runtime coverage without weakening any response validation.
- `delivery-runtime-python312.log` and `delivery-runtime-python314.log`: all 12
  runtime tests passed on the final code in 15.038s and 13.119s, including the
  null-versus-404 path and unchanged ancestry-identity diagnostics.
  `render-check.log`: wrapped locked renderer `--check` exited 0; no production
  registration, render or Builds pin changed.
- `final-local-checks.json`: frozen intent and original baseline preserved,
  source hashes, SDK/C# and owned-boundary checks, unchanged default
  authentication, evidence credential scan and whitespace checks. This is
  local readiness evidence; the committed adoption-candidate/global checks and
  live checkpoint remain unperformed.
- `recheck-preflight.{py,json,log}` and `module-fetch.log`: authenticated live
  GET observations, exact failure and remotely reachable source revisions;
  no provisioning or delivery claim follows from these reads.
- `app-selection-browser-blocker.json` and
  `pre-adoption-prepush-blocker.json`: fresh read-only authentication state and
  both exact failed mandatory module-check commands; no push was attempted.
- `resume-prerequisites.{py,json,log}`: 2026-11-16 authenticated maintainer
  preflight, exact browser URL/prompt, both failed check commands and successful
  Git tree inspection proving the legacy pin lacks the checker. No UI or remote
  mutation occurred; the default profile and absent overrides are unchanged.
- `app-selection-*.json`, `provision-*.{json,log}` and
  `provisioning-after.json`: actual saved App scope, stale configuration/tag
  cleanup, exact protections, main-only environments and scoped Zot credentials,
  including preservation and real registry outcomes. `provisioning-status.md`
  separates completed administration from pending policy/grant and adoption work.
- `nuget-commons-{proposed,submit,readback}.json`,
  `nuget-session-expired.json` and `nuget-signin-result.json`: exact failed
  creation/readback and subsequent human authentication boundary; no saved
  additive NuGet policy is claimed.

Remaining verification for adoption:

- `run-with-temp uv run --locked --script tools/tests/test_deliver.py` — compatibility and delivery behavior pass on Python 3.12 and runner Python.
- Builds publisher regressions, module package-mode builds/tests and Commons consumer checks — pass with saved logs; no workflow-text assertions.
- Wrapped `tools/render.py --check`, render/validate suites and `tools/check_global.py` with their locked script environments — pass for the committed candidate.
- Inspect authenticated delivery/nightly artifacts, live settings/policies, feed verification and probe cleanup; fixtures do not prove live acceptance.
