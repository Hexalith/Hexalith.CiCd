# Works registration — 2026-11-19

Story 11 nightly checkpoint is accepted (spec 11 status `done`). Product
preparation is on live Works `main` `4053907d5764bc8833c95dd79ea337bc8faba159`
(tree includes `.github/actions/{after-unit-tests,platform-parity}/action.yml`;
tool-only npm/releaserc and YAML/story tests absent). The CiCd gitlink already
records that commit. Nested submodules were not initialized.

## Setup

`setup/Hexalith.Works.yml` registers `Hexalith.Works.slnx`, `dapr: true`,
`additionalSdkVersion: '10.0.404'`, CodeQL `csharp`/`python`, hook
`after-unit-tests`, Linux job `platform-parity` (`timeoutMinutes: 180`,
`setup.dapr: true`), and submodules `references/Hexalith.{Platform,Parties}`.
`builds-version` remains `v6.4.2`. Shared `ciTimeoutMinutes` stays the schema
default 30. Nine Explicit Platform-lane facts stay in IntegrationTests; stage 4
is not given a skip list.

## Render

`run-with-temp uv run --locked --script tools/render.py --check` exit 0 after
writing `rendered/Hexalith.Works/**` and `rendered/Hexalith.Works.perimeter.json`.
The CI caller forwards `additional-sdk-version` and hosts `custom-platform-parity`
on `ubuntu-latest` with a 180-minute timeout and independent Dapr job setup.
No `qualification.yml` (the extra job is CI-triggered).
