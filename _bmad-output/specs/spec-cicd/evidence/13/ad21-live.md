# Story 13 AD-21 live readbacks — 2026-11-17

App selection, stale-state cleanup, rulesets, main-only `hexalith-release`,
Works Zot identity, additive nuget.org policy, scans, publish switch, retention
and org grants. Story 11 night was not dispatched. Setup/render/gitlink wait.

## App selection

Installation `179966090`, selected-only, Save disabled. `Hexalith.Works` already
present; no selection write. Evidence: `app-selection-verified.json`.

## Cleanup, rulesets, environment

Stale CodeQL analyses for `.github/workflows/codeql.yml:analyze` deleted.
Unpublished tag `v1.0.0` (`525279ac279636d4141e419e643f741dc2a00519`) deleted
after nuget.org showed no 1.0.0 packages. Releases `v1.0.1`/`v1.0.2` kept.
Created exact `Protect main` and `v tags`. Created main-only `hexalith-release`
beside existing `production`.

## Registry and NuGet

Zot user `hexalith-works-publish` for `works`/`works/**`; environment secrets
set; foreign writes 403. Additive policy `Hexalith.Works hexalith-release`
(`27451`): `release.yml`, environment `hexalith-release`, glob `Hexalith.Works*`,
push only. Legacy policy `20087` (`production`, glob `*`) unchanged.

## Settings

Default CodeQL setup `not-configured`, Dependabot security updates off,
`HEXALITH_RELEASE_PUBLISH_ENABLED=true`, retention 90 days, secret scanning
push protection enabled. Granted selected pull secrets and `HEXALITH_NUGET_USER`.
Immutable releases still off; legacy publishing access retained until adoption.
