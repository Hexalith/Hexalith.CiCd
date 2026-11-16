# Story 14 local implementation results

This report preserves the earlier local qualification. See
[preparation publication](../publication/README.md) for the subsequently authorized
main publications, fresh-main integration and updated test counts.

Status: **in progress**. No commits, pushes, remote administration, release,
production registration, delivery, credential cleanup or scheduled-nightly
acceptance were performed.

The approved six-path amendment is applied. The full local product proof now
passes: **6288 tests, zero failures, zero skips**, plus six packages and seven
isolated consumers. See [the approval and verification record](approved-exclusions.json).

## Exact candidates

`final-candidates.json` captures canonical Git source trees without changing real
indexes or HEADs. Both match the full ordered native product qualification:

- Agents base: `895039d8513363424882b3b7d64bca574fddc43b`.
- Agents candidate tree: `c11d75c7d81d133e9a87a7d92b3e4316a1597ce4`.
- Builds base: `fdda17c0a4538b0f7c99f813c20ca24b49006530`.
- Builds candidate tree: `e4540657efe3d1eedc989398ae826c310f47eeda`.

These are local source trees, not released tags or pushed product revisions.
The manifest records every changed path and hashes all saved logs.

Before approval, [parent verification](parent-verification/README.md) corrected
three shared fixture builders and removed formatting churn. That report and
`final-candidates.before-approved-exclusions.json` retain the earlier source
identities. The current identities above include the approved exclusions and
the hosting-guard follow-up described below.

## Passing local verification

- Python 3.12 and runner Python 3.14 each pass 18 schema/reader tests,
  38 pipeline tests and 38 local-check tests for the shared runtime policy.
  Native fixtures exercise count boundaries, fail-skips, project completion,
  stop ordering, default behavior and CI/local parity.
- SDK 11.0.100 package-mode Release restore/build passes with audits enabled,
  warnings as errors and SDK/net11/C#15 preserved.
- The full ordered suite passes Contracts 2005 (floor 529), Client 7 (floor 6),
  domain 1041 (floor 787), Server 1883 (floor 549), and UI 1352 (floor 1073).
  All five suites retain fail-skips and complete-project execution.
- The real hook packs six packages without rebuilding/restoring Agents, then
  validates all archives/UI assets and compiles seven isolated consumers.
  It retains no receipt and its reserved scratch is absent afterward.
- 67 focused package, archive, consumer, pack, publish, recovery and exact-exclusion regressions
  pass. The generic CLI entrypoints keep their configurable behavior; the hook
  imports reusable validation and uses explicit literal compiler commands.
- The unchanged production source-discovery engine selects six complete hook
  sources with no errors. No scanner rules or detector policy were changed.
- Released audit lint passes. Owned module bytes/modes and the Builds gitlink
  exactly match the recorded Agents base. Fresh-main verification remains pending.
- Locked `tools/render.py --check` and diff whitespace checks pass.

## Resolved authority decision

The human approved the six exact historical nonproduct paths in
`historical-authority-decision.md`. Only those paths were added to the existing
exclusion inventory. Original entries and all historical source bytes are
preserved; `approved-exclusions.json` binds their hashes. A focused regression
requires the exact six additions and keeps maintained projects outside the
exclusions. The full authority check now passes.

The first rerun exposed a stale validator filename in the hosting product
guard. Its existing policy-data exception now follows the same validation code
into `nuget_package_validation.py`. All hosting product checks remain. Its
registered nested-submodule automation scan was removed under the established
rule against agent/workflow checks in module gates, so Server has one fewer
registered nonproduct test. All original test floors remain unchanged.

Original failed results remain in `full-suite-failed-authority.{json,log}`
and `post-approval-hosting-path-failure.{json,log}`. They are historical failures;
`product-results.json` records the complete passing ordered rerun.

## Pending acceptance

1. Refresh current mains and AD-21 authenticated provisioning evidence with the
   intended credentials, including App scope, stale drafts/tags, rulesets,
   environment, identity/policy, grants, scans and retention.
2. Obtain pilot acceptance and an acceptable Builds release containing the new
   strict test policy and central audit treatment; retain current `v6.0.6` until
   that prerequisite is met.
3. Revalidate preparation against freshly fetched main, validate exact commit
   messages with released tooling, and save exact base/head proof before pushes.
4. Qualify the complete cross-module duplication scope, commit cause/output,
   register the candidate YAML, render with the accepted tag, and run committed
   global/live validation. `Hexalith.Agents.yml` here is a proposal only.
5. Authenticate App delivery and require the normal standalone module checker;
   then perform immediate credential/policy cleanup and immutable-release setup.
6. Verify green CI and Agents' next genuine scheduled nightly outcome, including
   both CodeQL languages. No such outcome is inferred from this local run.
