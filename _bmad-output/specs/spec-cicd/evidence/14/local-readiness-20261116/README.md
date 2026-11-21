# Story 14 local readiness, 2026-11-16

> **2026-11-21:** the runner scripts this record used were removed from git under the AGENTS.md Evidence rule. Their blob ids and SHA-256 values, and how to recover them, are in `../removed-runners.json`.

Story 14 remains **in progress**. This resume ran sequential local qualification
without GitHub reads, remote repository operations, provisioning, release,
registration or delivery. It preserves the already published preparation and
every concurrent workspace change.

## Passing checks

[`regressions.json`](regressions.json) binds exact local committed snapshots and
hashes the saved logs. In disposable `run-with-temp` clones:

- Builds `6db97d4e9da392ef691ed3f367e73f1b7d2ef318` passes schema (18),
  executor (38) and local-check (38) tests on both Python 3.12 and 3.14.
  This includes native count/skip and complete-project/failure-order coverage.
- Agents `c5c22620cafaa0af2625896cf41022e614e9b490` passes 67 focused
  package, consumer, archive, scratch-cleanup and exact-exclusion regressions.
- Agents remains clean, and its owned byte/mode/gitlink diff against the recorded
  preparation base `805b35da01efe4d3ac5f1402e611950ac282d0a1` is empty.

The earlier [6325-test/six-package/seven-consumer publication proof](../publication/README.md)
still names the current Agents source. It qualified Builds
`26031f097198f001380c23f4b9fb855c3d7b88c6`, not the
newer shared source checked here. Full ordered product and package/consumer proof
must therefore be refreshed against the selected acceptable release before the
next preparation push or adoption. No new full-product pass is claimed here.

## Incomplete cross-module scan

[`scan-scope.json`](scan-scope.json) and the unchanged production scanner's
[`scan/report.json`](scan/report.json) record a disposable prospective registry
containing the two registered pilots and Agents. The exact local module commits
are recorded; no live-main freshness is inferred.

The real locked jscpd 5.4.3 / TypeScript 6.0.3 detector installed and verified
all npm signatures with npm forced offline and a disposable copy of the existing
public cache. All scanner, parser, lockfile and policy sources match controller
`0f25d19ba712eee9aae59d118251b854bbffd120`; none was changed.

Agents has six selected reachable sources and no discovery errors.
PolymorphicSerializations has no action sources. Commons local snapshot
`49187d47da882d5470deac982bb383486c90202c` has four unresolved discovery errors:

- `.github/actions/after-unit-tests/action.yml:9`: shell command substitution.
- `.github/actions/after-unit-tests/action.yml:10`: computed `rm` operand.
- `scripts/pack-release-packages.py:47`: computed subprocess environment.
- `scripts/validate-consumer-package-references.py:159`: computed subprocess cwd.

The detector reports zero cross-module copies in the selected sources, but the
overall scan **fails because coverage is incomplete**. This does not qualify
hook enablement. Preserve scanner policy and obtain complete fresh live-main
coverage before production registration; resolve actual sibling-source failures
in their owning migration rather than infer that the local snapshot is current.

## Adoption prerequisites

[`readiness.json`](readiness.json) records only local objects and existing saved
evidence. The selected `v6.0.6` tag is
`fdda17c0a4538b0f7c99f813c20ca24b49006530`; its schema lacks both count/skip
fields, and its shared props lack the central NU1901/NU1902 treatment. No locally
known tag contains the recorded shared-policy preparation commit. Remote release
state was not refreshed, so an acceptable release remains unverified.

Pilot story 11 is still in progress pending its genuine scheduled-night
checkpoint. Agents has no production setup file. AD-21 authentication and
provisioning, acceptable release selection, fresh full qualification,
registration/render/global/live validation, App adoption, the ordinary standalone
checker, immediate legacy-access cleanup, green CI and Agents' next genuine
scheduled nightly all remain required. This resume does not remove or weaken any
of those conditions.

Reproduce the local checks from the CiCd root, sequentially:

```bash
run-with-temp python3 -B _bmad-output/specs/spec-cicd/evidence/14/local-readiness-20261116/qualify.py
run-with-temp uv run --offline --with PyYAML==6.0.3 python -B _bmad-output/specs/spec-cicd/evidence/14/local-readiness-20261116/scan-local-snapshot.py
run-with-temp python3 -B _bmad-output/specs/spec-cicd/evidence/14/local-readiness-20261116/record-readiness.py
```

The scan command intentionally returns nonzero while coverage is incomplete.
Each command waits for child work and removes disposable clones, caches and
outputs; the reports and useful logs remain beside this document.
