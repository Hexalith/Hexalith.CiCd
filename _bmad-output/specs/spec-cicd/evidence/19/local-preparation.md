# Story 19 local preparation — 2026-11-16

Status: locally prepared, incomplete. The initial preparation below describes local commit `bf0f44ff395d89c5565a423b424e389d2f80d0f6`; subsequent fixes and verification are in progress. Authorized GitHub reads and a push dry run have since run, but no remote ref, adoption, delivery, release or credential revocation has changed. No nested submodule was initialized. The separate long-running nightly prerequisite remains unreleased/unverified here; CiCd still pins Builds v6.0.6 with its 45-minute hook default.

## Current follow-up

The initial composed-graph MSB3277 diagnosis and unauthenticated-module verdict below are superseded. Canonical acyclic snapshots of the pinned sources eliminate the assembly conflicts; the earlier scratch topology caused them. The existing module-agent credential is now configured in its intended profile and authenticated repository reads and a main-push dry run pass. No new credential or broader permission was requested, and no remote ref changed.

The final local checks pass 5,388 unit tests, 18 AppHost tests, 548 ordinary integration tests and 289 UI E2E tests, with exactly the unchanged manual observer case unexecuted. Three required live cases and both release cases execute and fail at the pinned SDK's owner-loader guard: the test host loads app-local Json11, while the normal net10 owner relies on framework10. The normal output lacks a Json package/DLL, and the public loader refuses the host-local fallback. No guard, runtime, dependency pin or assertion was weakened. The configured private-custody path and matching published helper preserve the real compiled-owner contract, but actual catalog enrollment and custody receipts remain unverified because owner loading refuses first. Fresh private tmpfs backends and their cleanup were observed; no observations were fabricated.

The runtime snapshot and final source differ only in the existing Architecture test's helper-mode/required-metadata assertions. The final version passed a fresh package-mode build with zero warnings/errors and all 119 tests. Other lane evidence is inherited only through that documented sole-file delta; old hashes are preserved. Complete proposal patches and their tree identity are recorded in `product-proposal-patch.json`. All owned verification work/resources have finished. See [final product verification](product-fix-verification.md), [parent audit](parent-fix-audit.json) and [current progress](fix-progress.json).

Required runtime checks now occupy a whole `Live.IntegrationTests` project with runner-enforced `failSkips`. The existing manual independent-observer producer stays unchanged and visibly optional in ordinary integration; missing independent enrollment is reported as unexecuted, and every other unexpected skip fails verification. Positive committed-state M2/origin-parity checks remain whole-project nightly release gates; Sunday recovery remains separate. All required live/release/recovery projects reject skipped tests. The existing production atomic-participation refusal remains an independent source-proven release blocker, without changing expected state or inventing owner capability. The live/release scenarios currently stop earlier at the observed loader refusal.

The separate timing prerequisite must preserve the original 330-minute recovery/preparation/cleanup capacity plus the legacy 30-minute release-gate allowance, for 360 minutes total while retaining the 45-minute default. Registration and adoption remain blocked until that shared capability ships. AD-21 administration is prepared but waiting for GitHub's owner-browser “Confirm access” step; the maintainer installation-selection API returned a recorded 403. No requested setting is represented as applied.

## Initial preparation record

## Product preparation

The ChatBot working tree remains based on `6a4ca07b18e9b58500dc79dfede1f308da36c828`. Removed the story-evidence executable, its test project/policy, obsolete legacy pipeline scripts and their tests, semantic-release/commitlint-only npm files and `.releaserc.json`. Removed workflow/ledger assertions from mixed architecture tests, retaining their package/container inventory, SDK, topology, sandbox and compiled dependency checks. The legacy owned workflows remain byte-identical and still reference the retired tooling until App adoption replaces them.

Removed direct sibling library projects from `Hexalith.ChatBot.slnx`; retained all declared AppHost executable/composition references and ordinary package-mode library references. Preserved SDK 11.0.100 and selected Microsoft.Testing.Platform after reproducing DW-4 with the default VSTest path. The AppHost downloads the already manifest-pinned module-tool package during NuGet restore and forwards its published Tooling DLL location into composition references. Cold evaluation covers the default cache, NUGET_PACKAGES, RestorePackagesPath and explicit NuGetPackageRoot, including the resulting Platform reference without a Builds.Tooling source-project edge. Full graph execution after this final binding correction is still unverified.

Added `Hexalith.ChatBot.Recovery.Tests`, whose sole discovered test invokes the unchanged recovery scenarios through the internal integration harness `LiveRecoverySweep`. Ordinary integration retains its recovery contract, failure-boundary, loader and cleanup tests. Only the superseded downloaded-artifact release-gate entry point was removed from the mixed replay test class. No Server/Audit recovery implementation was removed or changed.

Added dormant module-owned `after-unit-tests` and `nightly` composite actions. They consume the shared built Docker/Dapr/Playwright environment, require a real browser, enable required live topology flags and preserve published composition inputs for Aspire child processes. The Sunday UTC hook runs the whole dedicated recovery project, with a 250-minute in-process deadline, interrupt at 280 minutes, kill grace and 300-minute outer command limit. Failed/invalid UTC date resolution and due-test failures propagate as failures. Registration must assign this project to `nightly` with `tests.exclude`, keep ordinary integration in CI and supply the separately released 330-minute hook allowance. These actions are not enabled yet.

Fixed the existing generated-client freshness fixture: its expected hash disagreed with the checked-in client before this patch. Normal NSwag generation matches the baseline client byte-for-byte; only the stale hash fixture changed, and its assertion remains intact.

## Verification

Disposable repository copies, package/source snapshots and build outputs were created under `run-with-temp` workspaces and removed after child completion. Dependency snapshots came from locally available root-declared Git objects at ChatBot's exact gitlink revisions, without nested checkout initialization or remote reads. No credential was used or changed.

| Check | Result | Evidence |
| --- | --- | --- |
| SDK 11.0.100 runner probe, exact catalog xUnit 4.0.3 | Default VSTest fails; MTP executes 1 passing test, zero skips | `runner-probe.log` |
| Referenced test-project discovery probe | Recovery project runs only its own test, 1 pass, zero skips | `recovery-project-discovery.log` |
| Architecture / Contracts / Server / Conformance / CLI / MCP / Testing / UI / Workers | Respectively 119 / 531 / 3629 / 151 / 61 / 70 / 41 / 613 / 32 pass; zero failures/skips | `focused-product-verification.log` |
| Client original full lane | 140 pass; one stale freshness-fixture failure, zero skips | `focused-product-verification.log` |
| Client corrected fixture | Normal NSwag regeneration is byte-identical to baseline; exact focused assertion passes, 1/1 with zero skips | `client-freshness-verification.log` |
| Runtime/cadence contract fixtures | Nine original cases plus date failure, invalid weekday and missing weekday pass | `custom-action-contract.log` |
| Final cold tool-path and Platform evaluation | Four package-cache cases pass; every root is absolute, selected assembly exists, Platform has no source Tooling reference | `composition-reference-evaluation.json` |
| Deterministic existing CiCd render | Pass; no ChatBot registration/render created | `render-check.log` |
| Ownership preservation | Seven tracked owned/partially owned whole files and 16 gitlinks unchanged; zero nested checkouts initialized | `local-ownership-verification.json` |

`package-mode-verification.log` and `composed-baseline-comparison.log` preserve **superseded failed attempts**, not green verification of the final tool binding. Those attempts reproduced MSB3277 conflicts in both the baseline AppHost and current graph using a defective cyclic/duplicate scratch layout. The later canonical acyclic source snapshot eliminated the conflicts; the failures do not establish a product defect. No pruning/audit/test suppression was added. Earlier attempts also exposed the now-corrected relative published-tool root. Cold reference evaluation alone does not certify the graph or live behavior; consult the follow-up proofs for each actual verified snapshot.

These product checks used ChatBot's existing Builds gitlink `6ad5854aa14a9950e1fbfc32d7e27953a1c4b82b`. They do not establish product compatibility with CiCd's selected `v6.0.6` or the future prerequisite release, whose catalog may change the composed graph. The renderer check against CiCd's selected release does not substitute for that product verification.

All broad verification subprocesses have exited. The unit loop finished normally; a workspace-scoped watchdog imposed a 300-second command bound and cancellation grace (`verification-watchdog.log`). Later focused jobs have explicit 10–120-second subprocess bounds. Whitespace validation uses command-local `core.whitespace=cr-at-eol` to preserve authored recovery CRLF bytes.

Parent inspection independently matched the final patch/new-file hashes to the refreshed ownership proof and verified the seven protected files, all 16 gitlinks, unchanged recovery scenario body, solution boundary and approved frozen intent (`parent-local-audit.json`). Story acceptance and formal review remain incomplete. The changes are local and are not certified for pushing.

## Remaining acceptance

Resolve the baseline composed-graph product failures and rerun the complete approved pre-adoption procedure on the exact remotely pushed revision. Verify live Docker/Dapr/browser execution, the dedicated recovery project's compilation/discovery and every recovery scenario/cleanup boundary. Keep the standard checker mandatory after adoption.

Independently verify the released nightly-hook prerequisite and AD-21 App selection, rulesets, release environment, module-only Zot identity, NuGet policy, publish switch and shared organization access. The old preflight is a planning snapshot, not a current absence/access verdict. Register/render only after these prerequisites and a remotely available product revision; include the executable/composition source dependencies and source-read dependencies (notably FrontComposer and Timesheets). Run authenticated committed-candidate validation, App adoption/perimeter and foreign-content checks, immediate legacy credential cleanup, hosted green CI and the next central nightly outcome. None of those external acceptance steps is complete.

## Push request follow-up

The human subsequently authorized pushing all story 19 changes to main. Freshly fetched ChatBot main remained `6a4ca07b18e9b58500dc79dfede1f308da36c828`. Product preparation is preserved in local commit `bf0f44ff395d89c5565a423b424e389d2f80d0f6` on `story/19-chatbot-product-preparation`; the committed patch is byte-identical to the inspected patch. The message passed locked, signature-verified commitlint (`product-commitlint.json`).

The initial preflight found no configured GitHub host in `/home/administrator/.config/gh-module-agent`. The follow-up found the existing credential and configured that intended profile; repository reads and a main-push dry run now pass. The original preflight remains historical evidence, not a current access verdict. Successful command-local maintainer metadata reads confirm no ChatBot rulesets, no environments and no `HEXALITH_RELEASE_PUBLISH_ENABLED` variable. The approved pre-adoption build/test exception and AD-21 settings remain incomplete. These are push blockers independently of the nightly capability's separate adoption dependency.

No product push or CiCd commit was attempted. The unpublished product gitlink remains unstaged; CiCd notes and evidence remain staged locally. The shared Git instructions require stopping before the superproject commit when the submodule cannot be published. Authentication and precondition results are recorded without credentials in [push preflight](push-preflight.json). The earlier no-remote-operations statement describes the implementation phase; this follow-up performed the explicitly authorized read-only preflight, with no remote write.
