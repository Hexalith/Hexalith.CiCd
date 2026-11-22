---
title: Reconcile organization-wide CiCd App access
type: chore
baseline_revision: 5883ebcb4dde154ec67d044c778fcccc355c7c33
created: '2026-11-22'
status: done
---

# Story 30-3. Reconcile organization-wide CiCd App access

The maintainer approved **All repositories** for the active Hexalith CiCd App on
22 November 2026. The approved policy covers current and future organization
repositories. AD-7 defines the installation and job token boundaries. AD-21
verifies the installation mode at the organization level and retains AD-3's
repository-scoped access check during delivery. CAP-4 and CAP-16 continue to
define managed adoption. [Approved proposal](../../../planning-artifacts/sprint-change-proposal-2026-11-22.md)

- [x] Reconcile the architecture, specification, enforcement, module inventory
  and operator readback procedure with the approved policy.
- [x] Record fresh hosted installation mode, grants and environment restrictions.
- [x] Verify the workflow inventory and mutation tests and compare workflow,
  policy, selector and managed perimeter identities against the baseline.
- [x] Close DW-38 against the approved mode. The original HTTP 403 and story 11's
  earlier Docs exception remain in their respective records. [Deferred-work ledger](../../../implementation-artifacts/deferred-work.md#dw-38-complete-current-app-selected-repository-membership-remains-unverified)

## Hosted verification

Read-only GitHub API requests used the command-local maintainer profile
`/home/administrator/.config/gh`, with `GH_TOKEN` and `GITHUB_TOKEN` unset.
The authenticated `jpiquot` membership was active with organization role
`admin`. The installation was active, `repository_selection: all`, App ID
`5671811`, slug `hexalith-cicd`, installation `179966090`. Its grants were
Actions, Contents and Workflows write, and Administration, Metadata and Code
scanning alerts read. The `cicd-app` client ID matched the installation and the
custom deployment-branch policy listed only `main`. These GETs establish the
hosted configuration. The offline check below establishes workflow source
scope. [GitHub installation](https://github.com/organizations/Hexalith/settings/installations/179966090)

Each read returned HTTP 200 on 22 November 2026. Times are UTC and digests are
SHA-256 of response bodies. Environment paths are under
`/repos/Hexalith/Hexalith.CiCd`.

| GET endpoint | Time | GitHub request ID | Response body digest |
|---|---|---|---|
| `/orgs/Hexalith/installations?per_page=100` | 17:07:59 | `D4B7:342953:13F46BED:1E149D2E:6B03216F` | `bbd5382cbf66698ef56dfdf8915dee52411c5497a5d608f825ed6e13837a11b5` |
| `/user/memberships/orgs/Hexalith` | 17:07:59 | `D4C1:2F58A2:131E704C:1CC8C201:6B03216F` | `13a584c7c58b02c6862c2f4b5b88847f400c4f37b786ff2a371c674111217015` |
| `/environments/cicd-app` | 17:07:59 | `D4C3:35FB30:13606EA5:1D3E5301:6B03216F` | `62b5d307d91b9f2e0432c2cba4e16ce1bbf6438faf61e915f4dffb23a4350ca1` |
| `/environments/cicd-app/deployment-branch-policies` | 17:08:00 | `D4C5:1CDDC1:141F6F6B:1E4D655F:6B032170` | `fa563aefcf72e6b38b6932dcaa5e26a4d7c7263b58b9e63cd804dd6e304993ed` |
| `/environments/cicd-app/variables/HEXALITH_CICD_APP_CLIENT_ID` | 17:08:00 | `D4C9:35FB30:136074F7:1D3E5CB3:6B032170` | `33d9b6cfa44eee053fef18a81a47163efcf225fccf65cff29278ce1330e6ac1b` |

## Source verification

Both locked commands ran with `run-with-temp`.

| Command | Result | Log SHA-256 |
|---|---|---|
| `uv run --locked --script tools/check_app_inventory.py` | Pass, 7 workflows, 10 jobs, 76 reviewed mint steps | `cab51597e110aee7f381529c56d13f41fdbdf9f948888c7289bdd3a2cfb9d22b` |
| `uv run --locked --script tools/tests/test_app_inventory.py` | Pass, 17 tests | `9c0757ef7c5a6543ed5924bd27abdb8951167c494d7a90d4de1fd96630008915` |

The implementation worktree matches baseline
`5883ebcb4dde154ec67d044c778fcccc355c7c33` (tree
`c67f12891a92b4653add6deb7e99aeff669cecb6`) for these paths.

| Path | Baseline and implementation Git identity |
|---|---|
| `.github/workflows` | `559044e0931908fab4f351f8b67addc99dd103b6` |
| `tools` | `f2d89edd95ab9f23905d3a65419b50ce72f77ecc` |
| `tools/app-workflow-policy.json` | `414ab95013dcabc715f8a85ae6db271b54681373` |
| `setup` | `bb299f775e8564d7dc873f21a5abe10952e4d15c` |
| `rendered` | `d1c499bd45fe6ae9e832e2144d9e4a6360db1d40` |
| `templates` | `6a2337c8dee8cc4dbae9c9687bf00b21c96e8075` |
| `builds-version` | `ecb8b9a7d5cd90f97c08600ef5730590df82cdc4` |
| `.gitmodules` | `5f4db08e8b4a26baaa3649160a7ddf3f8c5e1b0c` |
| `references` | `ac32f4ff974919a21ba9b460d33d252d270e3702` |
