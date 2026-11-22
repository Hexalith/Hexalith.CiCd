# Story 11 execution reconciliation — 2026-11-22

**Result: incomplete.** Historical pilot acceptance dated 2026-11-19 remains
preserved. The independently rejudged nightly passes both pilots and the pilot
checkpoint, but current AD-7/AD-21 installation scope fails and required settings
and NuGet visibility remain unverified. This run does not renew acceptance.

## Current maintainer preconditions

The command-local maintainer profile `/home/administrator/.config/gh`
authenticated `jpiquot` (ID `6775094`). The default remained CiCd-agent;
`GH_TOKEN` and `GITHUB_TOKEN` were absent from the inherited environment.
Sixty-two GET request identities/digests are recorded separately from their
setting verdicts in `current-maintainer-receipt-20261122.json`.

- **Fail:** Cursor installation `182926560` and Codex connector `77847816`
  still select all repositories. No installation mutation occurred. Preserve
  unrelated selections when repairing Cursor exclusions. The connector's exact
  intended module selection is not established by an all-repository inventory;
  do not infer it or remove another repository's grant.
- **Unverified:** CiCd App `179966090` exact membership. Intended-profile GET
  `user/installations/179966090/repositories?per_page=100` returns HTTP 403,
  request `D260:1703:6EF8695:A750AF1:6B02DF41`: “You must authenticate with an
  access token authorized to a GitHub App, a personal access token, or basic
  auth in order to list repositories for an installation.” Accepted scopes
  report `read:user, user`; profile scopes are `admin:org, gist, read:packages,
  repo, workflow`. Account administrator status does not resolve token access.
  Existing browser navigation to its exact installation-settings URL reaches
  **Confirm access**. Attended GitHub authentication/settings access is needed;
  no authentication control was invoked, token broadened or App key obtained.
- **Unverified current NuGet scope:** cached browser cards show original scoped
  policies `27048`/`27049`, but an explicit reload of the same native browser
  window redirects to `nuget.org/users/account/LogOn` with document **Sign In**.
  Cached cards are not current authenticated scope proof. Current sole policy,
  package-ID and legacy-key scope verification needs an authenticated NuGet
  session. Keep legacy key `954800` as historically Expired and unmapped;
  no fresh removal, secret mapping or current scope is claimed.
- **Pass:** both pilots' exact main/v-tag rulesets; main-only `hexalith-release`
  with only their dedicated registry pair; unchanged provisioning-era secret
  timestamps; both dedicated Zot ACLs (read/create/update only their own
  namespace, neither administrator); immutable releases; release switch `true`;
  disabled default CodeQL setup and Dependabot security updates; push protection;
  repository/org retention; org workflow/fork settings; required pull/NuGet
  grants and complete legacy-secret exclusions. Repository Actions/Dependabot,
  production-environment secrets and deploy keys are empty. Stored secret values
  are unreadable; the original provisioning identities plus unchanged metadata
  remain the environment-binding authority.
- **Pass:** complete releases/tags contain no drafts or orphan version tags
  (Commons 87/87, Poly 61/61). Current analysis inventories contain no legacy
  `.github/workflows/codeql.yml:analyze`; current release CodeQL and unrelated
  SonarCloud records are preserved. Zot ConfigMap resourceVersion is `49008107`.
  The previously accepted package-only legacy Zot no-op remains bounded to these
  pilots; global administrator/key mappings remain unverified.

## Independently qualified completed work

`source-and-probe-revalidation-20261122.json` records 32 GET response identities
and digests, local immutable Git identities, and the preserved evidence digests.
All nine planning-bound evidence digests match. The legacy completed spec keeps
blob `e71dcb4661c23e6e9a3a06fdc1357215b55afd9d` unchanged.

Both pilots' historical base/probe/preparation/adoption/fresh-product/update
commits and trees match current GitHub objects. Pre-delivery workflow trees are
equal; actual delivery changes them. Fresh product heads parent actual adoption,
and saved successful pushes/readbacks follow normal standalone checker exit 0.
Both actual Update branch operations returned HTTP 202; resulting parents match
`[pre-delivery probe, adoption]`, and complete adopted trees differ only by
`pilot-ci-probe.md`. PRs 52/19 remain closed unmerged; all recorded local/remote
probe refs are absent. The stale `remote_push_performed:false` flags remain
visible beside successful push/readback/cleanup evidence. Exact failed-CI log
digests and service merge messages confirm strict commitlint rejected those
merge heads (`subject-empty`, `type-empty`); product stages did not run there.

Registration commit `ba62ae71d148d3c5951f4508f7ebaf1bf49ab858` contains both
preparation gitlinks, setup and render together. Its child
`f002539f6fbaddaa9b621a9cbf75a1263eee5dea` corrects only the renderer fixture and
is the actual delivery source. Actual delivery `43860977581` and scoped policy
redelivery `43869480499` still authenticate their original artifact digests.
Both `v6.0.6` and current `v6.6.1` remain published, immutable, authored by
`github-actions[bot]`, and ancestors of live Builds main. Selected schema,
perimeter-reader and Props identities come from the exact released tag.

Current remote-main source trees retain all original C# test paths (48 Commons,
8 Poly), both product hooks, Commons' twelve payload/symbol pairs and isolated
consumer, and Poly's later README round-trip hook. Tool-only root npm files and
`.husky/` are absent; tracked MSBuild/rsp/NuGet configs contain no module audit
waiver matches. Adoption preserves SDK pins; later source improvements are
untouched. No pilot NU190x waiver existed to migrate; no waiver is invented.
Commons' NU5104 packaging treatment stays distinct from release auditing.
Canonical, rendered and current delivered instruction blocks agree on GitHub's
Update branch allowance and the agent prohibition on importing owned CI/CD.
Renderer `--check` passes, exit 0, empty output SHA-256
`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
No policy change or redelivery is necessary.

## Read-only nightly result

The exact requested `run-with-temp python3 -I tools/nightly_acceptance.py`
invocation rejudges run `44566082537`, attempt 1, source
`6b413de903926c52a355472f018d3ebcdbc8e144`, for both pilots and
`--checkpoint pilot`: **exit 0, both modules pass, checkpoint pass**.
The compact receipt binds the four authenticated artifact digests. Both release
runs (`44566233481`/`44566277325`) report nothing to release, successful Release
CodeQL, and passing own scan rows. Bump is no-change; push/delivery-wait are not
run; keepalive passes. AI.Tools, Builds and McpCli failures remain separate from
the passing pilot rows. Scratch stdout SHA-256 is
`489ad21b380952c3334e4291e56ff03003e7e3ef4940dea24e66ba5b6d856eed`;
raw output was removed with its disposable workspace.

This run creates receipts and this reconciliation only. It makes no remote
mutation, product change, adoption, probe replay, release dispatch, commit or
push. No new module push requires checker execution. Acceptance remains gated
on authenticated settings access, scoped installation repair/readback and
current NuGet scope verification.

## Receipt SHA-256 identities

| Receipt | SHA-256 |
| --- | --- |
| `current-maintainer-receipt-20261122.json` | `80dc2b0b2712ffb89c05ad7af24340d9c057331f185da432bb0f37d7680b5944` |
| `current-settings-ui-readback-20261122.json` | `65e22afd1b7e78d2f06093e6a2400d410c447235f180791e40ef1eb748d84f59` |
| `current-nuget-readback-20261122.json` | `9e2039f870c053f7773dd865b20f78d9c194b200decdd6a8aa19cb053fce9826` |
| `source-and-probe-revalidation-20261122.json` | `77e2c4486b8e2042fbafc8d4768139329f11622fb556bc3e04ed12d509e87a27` |
| `checkpoint-revalidation-receipt.json` | `88ad73321566120dfa2421c3bf58e3a1df60b408a3afe676fa4abdfffec3a016` |
