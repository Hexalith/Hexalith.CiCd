# Story 14 registration preparation, 2026-11-21

Story 14 is still **in progress**. For this run the human allowed remote reads
only (`git fetch` and `gh` GET requests). No commits, pushes, PRs, dispatches,
delivery, provisioning or credential/setting changes were made. Registration
is prepared in the primary CiCd working tree for the human to publish later.
This is not adoption.

Exact identities, results and log digests are in
[`qualification.json`](qualification.json). The maintainer readback is in
[`ad21-refresh.json`](ad21-refresh.json). Raw logs and the disposable runner
scripts stayed in session scratch; only their SHA-256 digests are recorded.

## Fresh state

- CiCd local `main` equals `origin/main` `399b2f2d9102649e17b0017c4da26e07e8d4f991`.
- Agents `main` is `0d03363bef95c0feecc136579b843f4cbcd34a21`. It still contains
  the prepared `after-unit-tests` hook. The committed CiCd
  `references/Hexalith.Agents` gitlink already records it, so the gitlink is
  unchanged.
- `builds-version` `v6.4.4` (`fe68718b6c074a6b500a7191e3554a1d39e17688`) is
  acceptable to the global check. It contains `tests.minimumExpectedTests`,
  `tests.failSkips` and the central NU1901/NU1902 treatment.
- Story 11's pilot checkpoint was accepted on 2026-11-19.

## Prepared registration (uncommitted)

`setup/Hexalith.Agents.yml` contains `Hexalith.Agents.slnx`, CodeQL `csharp`
and `javascript-typescript`, the five exact project floors 529/6/787/549/1073,
`failSkips: true`, `tests.integration: []`, `tests.exclude: {}` and
`hooks: [after-unit-tests]`. It adds no submodules, Dapr, browsers, registry or
jobs. `tools/render.py` produced `rendered/Hexalith.Agents/` and
`rendered/Hexalith.Agents.perimeter.json`. These match Commons' shapes, with
the default 30-minute CI timeout. `render.py --check` passes on the working
tree.

## Validation of a disposable committed candidate

The setup and render were committed only in a `run-with-temp` clone (tree
`9f214544ce9f7fead03823aedfd561247f5919cf`). `render.py --check` passes there.
`tools/validate.py` (including `check_global.py`) exits 0 with
`{"global":true,"modules":["Hexalith.AI.Tools","Hexalith.Agents","Hexalith.Commons","Hexalith.Conversations","Hexalith.McpCli","Hexalith.PolymorphicSerializations","Hexalith.Works"]}`.
Every global check passed: committed inputs/render, bootstrap, reproducibility,
schemas/callers, acceptable Builds publication, online actionlint/zizmor and
the tool suites. Every module check passed, including live Agents action
availability.

## Fresh live-main duplicate scan (prospective registry)

`tools/scan.py` on that candidate reports **FAIL**. Its detector signatures are
verified, there are no global errors and it reports **zero** cross-module
findings. Agents passes: six hook sources, no discovery errors. Coverage is
incomplete because other registered modules fail discovery on live main:
Commons 2, Conversations 7, McpCli 100, PolymorphicSerializations 3 and
Works 23 diagnostics. The recorded AD-21 rule keeps registration blocked
until complete coverage passes. No scanner exception is approved or proposed.
Those diagnostics belong to the owning modules' migrations. The latest
scheduled production nightly (run `44715684274`, without Agents) also reported
`Nightly duplicate scan: FAIL`. Its per-module report artifact was not
downloaded.

## Product qualification after a simulated delivery

This is a disposable simulation, not delivery evidence. The tagged `v6.4.4`
perimeter library applied the rendered perimeter to Agents `main` in a private
index (simulated tree `72db87a6f82b5b5c850a7b4252a3e2ece952c0c6`). The changes
match the expected delivery: legacy workflows removed, owned files added,
release/commitlint files removed and the Builds gitlink moved to `v6.4.4`.
Foreign content was preserved. The tagged checker then ran through a local
accepted-branch transport:

- **Phase 1, delivered main.** The guard passes (owned perimeter,
  audit lint, actions and commitlint). The package-mode Release build succeeds.
  All five suites pass with fail-skips, zero failures and zero skips:
  Contracts 2005, Client 7, Domain 1086, Server 2121 and UI 1362, against
  floors of 529, 6, 787, 549 and 1073. The hook then **fails**:
  `eng/consumer-executable-assets.json` records the pre-delivery catalog of
  Agents' current Builds pin `6b6eb4ee` (EventStore 5.3.0, FrontComposer.Shell
  6.0.0), not v6.4.4's 5.4.0 and 6.0.1. The 11 unique rows differ only in
  version; every SHA-256 is unchanged.
- **Phase 2, version-only product fix.** A simulated module-agent commit from
  the simulated delivered main changes only those 39 version fields (blob
  `e3f4f873…` → `22f6b756…`). The guard, the same five suites and the hook
  then pass: `Validated six built packages and seven isolated package
  consumers.` The worktree stays clean and the hook scratch is removed.

The fix cannot land before delivery: the pre-delivery Builds pin still selects
5.3.0 and 6.0.0, and the module must not move the owned gitlink. The first
adopted CI will therefore fail at the hook until a module agent publishes this
reviewed baseline update from fresh delivered `main`. Local checker plus hook
time was about 5 minutes, well inside the 30-minute CI budget.

After delivery, `package.json` is a tool-only stub with an empty
`devDependencies` and the semantic-release override, and `package-lock.json`
remains. AD-21 step 2 assigns deleting both to the module agent. Agents main
restored them in `05ddee8` for the still-active legacy release.

## AD-21 readback (maintainer profile, GET only)

Already satisfied: public repository, push protection on, CodeQL default setup
`not-configured`, Dependabot security updates off, retention 90 days and
`HEXALITH_RELEASE_PUBLISH_ENABLED` exactly `true`.

Still required before publishing the registration (maintainer writes):

- Rulesets: none exist. Create the exact `main` and `v*` rulesets. Delivery's
  closed App checks require them, so the module check would otherwise fail.
- Stale state: drafts `v2.0.0` (446267591), `v1.2.2` (426297010) and `v1.2.1`
  (426274664); tags `v1.2.0` and `v1.1.0` have no release; legacy
  `.github/workflows/codeql.yml:analyze` CodeQL analyses remain. Assess them
  before deletion and preserve published `v2.0.2`, `v2.0.1` and `v1.0.0`.
- Create `hexalith-release` (main only) with the module's own Zot push pair, and
  add the package-scoped nuget.org policy. Neither the Zot identity nor the
  NuGet policies are readable through GitHub.
- Organization grants: Agents is absent from the Actions/Dependabot pull pair
  and the `HEXALITH_NUGET_USER` selections.
- App selection: unverified. `user/installations/179966090/repositories`
  returned HTTP 403 again, which is not evidence of absence.

After authenticated adoption: enable immutable releases (currently off), remove
other nuget.org policies, and remove Agents from legacy `NUGET_API_KEY`
(currently selected), the API-key package scope and the legacy Zot push.

## Other observations

The legacy Agents CI on `0d03363` fails in "Initialize root-declared
submodules". The recorded AI.Tools gitlink `f3b2b383…` is not available on the
AI.Tools remote. The rendered CI initializes only the direct Builds dependency
(`submodules: []`), so this legacy failure does not apply after delivery.

## Pending

The following remain open: the human's scan-coverage decision or the owning
modules' discovery fixes; AD-21 provisioning; committing and publishing the
setup with its render; authenticated App delivery; the post-delivery asset
baseline and npm cleanup product changes; green adopted CI; credential
cleanup; and a nightly run (CAP-13).
