---
title: '11 — Pilot migration: Commons and PolymorphicSerializations'
type: 'chore'
created: '2026-11-15'
status: 'ready-for-dev'
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
- [ ] `tools/deliver.py`, `tools/tests/test_deliver.py` — handle the observed disabled response; test false/true/malformed/404/authorization-error cases and sibling isolation.
- [ ] `references/Hexalith.Builds/Github/lib/release_publish.py` and its tests — add generic bounded live NuGet verification before finalization, reusing authenticated inventory and package identity parsing; preserve missing/indexing-delay/source-conflict coverage. Release through the interactive shared pipeline and await an acceptable tag before adoption.
- [ ] Both module `tools/` and root `package.json`/lockfile — after shared coverage exists, retire duplicated legacy verification code/tests/manifests and tool-only npm files using the module token. Let delivery remove owned legacy configuration/workflows.
- [ ] Commons `.github/actions/after-unit-tests/action.yml` and its three package scripts — retain payload/symbol and isolated-consumer checks without another module build/restore; fix consumer SDK/cache isolation and CI audit-off/package flags. Test real package consumption; preserve all C# suites.
- [ ] `builds-version`, `setup/Hexalith.{Commons,PolymorphicSerializations}.yml`, `rendered/`, direct gitlinks — pin released shared behavior, use each `.slnx`, enable Commons' hook and default C# analysis. Before adoption, create the disposable product-only probe branch/PR from current module main and record base/head. Render and validate one committed candidate before pushing; hooks must already exist on live main.
- [ ] `evidence/11/` — authenticate both delivery commits/refs/reports; immediately enable immutable releases and remove other NuGet policies and legacy secret/key/Zot access. Record green CI, the scheduled night and post-delivery branch/Update-branch outcomes; clean probes and confirm/correct 10-2 restrictions.

**Acceptance Criteria:**

- Given satisfied prerequisites, when delivery adopts the pilots, then both owned trees match accepted perimeters and product files/tests remain intact.
- Given missing or wrong-source published packages, when shared publication verifies the feed, then it cannot report successful GitHub publication.
- Given adopted main revisions, when restricted-token branch probes run, then actual server outcomes and complete cleanup are recorded without owned-file edits or probe merges.
- Given green pilot CI, when one real scheduled nightly finishes, then CodeQL, releases or valid no-release outcomes, scan, Builds bump/no-bump and delivery are evidenced before checkpoint acceptance.

## Implementation Notes

## Spec Change Log

## Review Triage Log

## Verification

- `run-with-temp uv run --locked --script tools/tests/test_deliver.py` — compatibility and delivery behavior pass on Python 3.12 and runner Python.
- Builds publisher regressions, module package-mode builds/tests and Commons consumer checks — pass with saved logs; no workflow-text assertions.
- Wrapped `tools/render.py --check`, render/validate suites and `tools/check_global.py` with their locked script environments — pass for the committed candidate.
- Inspect authenticated delivery/nightly artifacts, live settings/policies, feed verification and probe cleanup; fixtures do not prove live acceptance.
