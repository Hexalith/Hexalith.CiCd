# Story 14 preparation publication

The human explicitly requested publication of all prepared work to `main`.
Isolated publication branches preserve unrelated changes and start from freshly
fetched current main. The source worktree is `cicd-story-14`; no unrelated dirty
work in the original CiCd main worktree was included.

## Confirmed submodule publications

- Builds: `26031f097198f001380c23f4b9fb855c3d7b88c6`, based on
  `1f41d266bd4bd04acde7b64e8c907eb34233fe0f`.
- Agents: `c5c22620cafaa0af2625896cf41022e614e9b490`, based on
  `805b35da01efe4d3ac5f1402e611950ac282d0a1`.

Both normal fast-forward pushes were confirmed by remote readback, using
CiCd-agent for Builds and module-agent for Agents. No credential fallback or
force push was used. The CiCd publication records these already-published
commits after preserving the newer Projects G-6 delivery changes on main.

## Verification

- Builds' complete library suite passes 565 tests on Python 3.12 and 3.14,
  after locked npm installation and signature verification.
- Agents' freshly integrated Release proof passes 6325 tests with zero failures
  and zero skips: Contracts 2005, Client 7, domain 1042, Server 1919, UI 1352.
- All five original floors and fail-skips remain enabled. Six real packages
  and seven isolated consumers pass, and hook scratch is removed.
- Owned module bytes and Builds gitlink match freshly fetched Agents main.
  Released audit lint and exact-message validation with signed pinned tools
  and the owning commit policies pass.
- The ordinary checker was attempted with the committed Builds gitlink before
  qualification and refused the absent pre-adoption config. The approved
  preparation proof then qualified the planned shared source while preserving
  the committed module perimeter. This is not adoption or a normal-checker pass.

Canonical source revisions, command results, exact messages, profiles and push
readbacks are recorded in the adjacent JSON files. Useful command logs remain
in the source worktree's matching evidence directory.

The Builds publication was followed by audit correction
`44cb6dbc869c4d84713278d9c861c6f5ba60bec6`, preserving newer upstream runtime
and Timesheets catalog changes. Its owning incremental generator preserves all
317 package rows; the final deterministic catalog validator passes. The generator
regression suite separately failed its shim-readiness handshake in the timeout
fixture. That failure is retained; no limit, test or audit was weakened.

The final CiCd candidate runs the locked render, every core global check and
the Projects delivery, renderer and validator suites after the concurrent main
refresh. A separate complete global run on the initial committed source remains
recorded in `publish/root-qualification.json` in the source worktree. Its status
is independent: this report does not claim a complete global pass.

Agents' hosted legacy CI failed its old pinned-source assertion, and its legacy
Commitlint failed dependency installation. CodeQL passed. The first Builds hosted
run passed Python, .NET, sample, lint and API jobs but detected the stale audit
fingerprint corrected above. These publications do not claim green hosted CI.

## Remaining acceptance

Story 14 stays in progress. An acceptable Builds release, pilot acceptance,
AD-21 provisioning, full cross-module duplication qualification, registration,
App delivery, immediate legacy-access cleanup and a genuine scheduled nightly
outcome remain required. No module-owned CI/CD portions were edited, no package
release was dispatched, and no adoption state is inferred from these pushes.
