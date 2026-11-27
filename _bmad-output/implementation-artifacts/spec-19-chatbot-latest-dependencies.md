---
title: '19 follow-up: Move ChatBot to latest dependencies'
type: 'chore'
created: '2026-11-27'
status: 'in-progress'
route: 'dispatch'
review_loop_iteration: 0
context: []
baseline_commit: 'b00126c0a8d6159e7cb527282f9811eda9b852f4'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** ChatBot `main` (`0fd555f3`) already runs on `net11.0` and Builds `v6.8.1`, but its Builds pin (`bf8a28b4`), CLI tool (`6.7.0`), and 15 sibling `references/*` gitlinks lag CiCd's `builds-version` (`v6.8.5`) and latest local submodule `main` commits, and its package-mode build and live/release suites are unverified on that cohort.

**Approach:** Advance ChatBot from `0fd555f3` to Builds `v6.8.5` (`deccbc3b`, CLI `6.8.5`) and CiCd's current `references/*` commits, fix only incompatibilities required for zero-warning package-mode compilation, and verify the build, core suites, required live refusal cases, and release-gate loader clearance.

## Boundaries & Constraints

**Always:** Work from fresh ChatBot `main` (`0fd555f3ac5eabc3df7f5a4e1d35dcabbe2272e6`) in a dedicated local worktree; keep SDK `11.0.100`, `net11.0`, Aspire `17.0.0`, and every existing test and assertion. Keep story 19's topology exception (gitlink-pinned AppHost composition sources, libraries in package mode). Use Builds `v6.8.5` catalog versions; override a Hexalith version only if a dependency minimum or EventStore loader byte-identity rule requires it. Build and test in standalone copies under `run-with-temp`; keep raw logs under `$TMPDIR` and record only revisions, results, and SHA-256 digests in git.

**Never:** Edit ChatBot's other CiCd-owned files (`.github/workflows/*`, `.claude/settings.json`, `.github/copilot-instructions.md`, `AGENTS.md`, `CLAUDE.md`, `.gitmodules`, Dependabot). Never copy framework DLLs, weaken loader/auth/admission guards, skip or filter tests, edit sibling repos, initialize nested submodules, push or run remote ops, delete `StoryEvidenceGate` (belongs to `spec-19-migrate-chatbot.md`), or register/adopt ChatBot.

**Human decisions, 2026-11-27 (supersedes 2026-11-18/19 pins):**

- **Builds pin:** One-time pre-adoption move of `references/Hexalith.Builds` to `v6.8.5` (`deccbc3bcf4ed687ecf4d556ebe356fe57148777`) and `.config/dotnet-tools.json` `hexalith.builds.module.cli` to `6.8.5`. Every other owned file and `.gitmodules` stays byte- and mode-identical.
- **Sibling gitlinks:** Pin the other 15 `references/*` gitlinks to CiCd's current `references/*` `main` commits recorded in `targets-20261127.json` without remote fetches.
- **Atomic participation & M2/origin release cases:** Out of scope (ChatBot Story 1.8). Keep `ValidateAtomicParticipationAsync` and `Hexalith.ChatBot.Release.Tests` unchanged; both release cases must clear owner preparation and fail only at admission.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Package-mode Release build | Updated ChatBot on Builds `v6.8.5` and target gitlinks | `dotnet build Hexalith.ChatBot.slnx -c Release -warnaserror -p:UseHexalithProjectReferences=false` exits 0 with 0 warnings | Fix ChatBot code; if a sibling `main` breaks package-mode compile, record SHA and stop |
| Core product test suites | Standalone package-mode copy under `run-with-temp` | All unit, AppHost, Architecture, Integration, StoryEvidenceGate, and UI E2E suites pass; only the optional manual observer is unexecuted | Fix product; keep assertions |
| Required live topology cases | `Hexalith.ChatBot.Live.IntegrationTests` with `require-runtime.py` + `required-live.xunit.runner.json` (`failSkips`) | All 3 required cases clear EventStore owner preparation and pass, 0 skipped | Record exact refusal/failure; never weaken guards |
| Positive M2/origin release cases | `Hexalith.ChatBot.Release.Tests` with `require-runtime.py` | Both run, clear owner preparation, and fail at `ValidateAtomicParticipationAsync` | Record result + log digest; not a story failure |
| Owned-content preservation | Candidate tree vs `0fd555f3` | All 7 owned files byte- and mode-identical; `.github/{hexalith-ci.json,dependabot.yml}` absent; only `references/Hexalith.Builds` changes | Reject unintended owned changes before commit |

</frozen-after-approval>

## Code Map

- Target revisions and catalog defaults: [targets-20261127.json](../specs/spec-cicd/evidence/19/latest-dependencies/targets-20261127.json) — authoritative base SHA, all 16 `references/*` SHAs, and owned-path lists.
- ChatBot worktree to create: `/home/administrator/projects/hexalith/chatbot-story-19-latest` on branch `story/19-chatbot-latest-dependencies` from `/home/administrator/projects/hexalith/chatbot` (`0fd555f3`). Leave `references/Hexalith.ChatBot` and `/home/administrator/projects/hexalith/chatbot` untouched. Populate standalone `run-with-temp` copies via `git archive` from CiCd's local `references/*` stores.
- ChatBot build/composition files: `.config/dotnet-tools.json` (`6.7.0` -> `6.8.5`), `Directory.{Build.props,Build.targets,Packages.props,Solution.props,Solution.targets}`, `eng/ChatBot.Composition.{props,Restore.targets}`, `src/Hexalith.ChatBot.AppHost/Hexalith.ChatBot.AppHost.csproj`, `.github/actions/after-unit-tests/require-runtime.py`.
- Sibling contract check: `Parties` (`ca637a01`) and `Tenants` (`ce3aadd8`) `Directory.Build.targets` both admit `$(HexalithCatalogEventStoreVersion)` (`5.6.0` in `v6.8.5`).
- Keep unchanged: `ChatBotAdmissionEvidenceValidator.cs:372-379`, `RequiredTopologyTests.cs`, `GovernedStateReleaseGateTests.cs`, `LiveContinuityAspireE2eTests.cs`, and all 7 owned files.
- Prior evidence: [loader-proof.json](../specs/spec-cicd/evidence/19/latest-dependencies/loader-proof.json), [main-readback-20261119.json](../specs/spec-cicd/evidence/19/latest-dependencies/main-readback-20261119.json).

## Tasks & Acceptance

**Execution:**
- [x] `/home/administrator/projects/hexalith/chatbot-story-19-latest` -- create worktree on `story/19-chatbot-latest-dependencies` from `/home/administrator/projects/hexalith/chatbot` (`0fd555f3`) -- isolate edits from clean `main` and CiCd.
- [x] ChatBot `references/*` and `.config/dotnet-tools.json` -- apply all 16 SHAs from `targets-20261127.json` (Builds `v6.8.5` `deccbc3b`) and bump `hexalith.builds.module.cli` to `6.8.5` -- match approved `builds-version` and latest sibling sources.
- [ ] ChatBot `Directory.*`, `eng/`, `src/`, `tests/` -- resolve any compile, analyzer, or package-mode runtime breaks under `v6.8.5` with zero warnings and no weakened assertions -- keep Release build and test integrity.
- [ ] Standalone `run-with-temp` copy -- run Release build, all core suites, `Hexalith.ChatBot.Live.IntegrationTests`, `Hexalith.ChatBot.Release.Tests`, and owned-file comparison vs `0fd555f3` -- verify every matrix row and confirm zero leaked containers/processes.
- [ ] ChatBot branch `story/19-chatbot-latest-dependencies` and `_bmad-output/specs/spec-cicd/evidence/19/latest-dependencies/verification-20261127.json` -- commit verified ChatBot changes locally (no push) and record SHAs, owned-file check, test counts, and SHA-256 log digests -- preserve compact auditable evidence.

**Acceptance Criteria:**
- Given the updated ChatBot worktree on Builds `v6.8.5` and target gitlinks, when built in standalone package-mode Release (`-warnaserror`), then build passes with 0 warnings/errors and all core suites pass with zero unexpected skips.
- Given `require-runtime.py`, when `Hexalith.ChatBot.Live.IntegrationTests` and `Hexalith.ChatBot.Release.Tests` run, then 3/3 live cases pass (0 skipped) and 2/2 release cases clear owner preparation and fail only at `ValidateAtomicParticipationAsync`.
- Given the final candidate vs `0fd555f3`, when owned paths are compared, then all 7 owned files are byte- and mode-identical, `.github/{hexalith-ci.json,dependabot.yml}` remain absent, and only `references/Hexalith.Builds` changes among owned items.

## Implementation Notes

- Historical (2026-11-18/19, baseline `53857b9e`): Initial loader proof on `ddd385ec` / Builds `v6.3.1` cleared `System.Text.Json` but parked on Parties 5.3.x and Projects/Conversations. See [loader-proof.json](../specs/spec-cicd/evidence/19/latest-dependencies/loader-proof.json) and [main-readback-20261119.json](../specs/spec-cicd/evidence/19/latest-dependencies/main-readback-20261119.json).
- 2026-11-27 (baseline `b00126c0`): Created `/home/administrator/projects/hexalith/chatbot-story-19-latest` (`story/19-chatbot-latest-dependencies` at `0fd555f3`), applied all 16 `targets-20261127.json` gitlinks and CLI `6.8.5`, forwarded `Hexalith1BuildPackageProps`/`Hexalith2BuildPackageProps`, and updated `LiveCatalogFixture.cs` for `Projects 2067b57d` split artifacts (`diff_head_binary_sha256: 7cfb64b5...`). Held uncommitted: Release build (`-m:1 /nr:false`) passed (0 errors, 0 ChatBot warnings), 13/14 core suites + native/python gates passed (6,729 passed, 0 failed), owned files byte/mode-identical, and all 4 owners cleared preparation, but three upstream cohort blockers stop green Architecture/Live/Release acceptance: (1) `EventStore 5484fae6` (`360ed041d`) vs published `5.6.0` `SubmitCommandResponse` schema drift (`ObservedRouteCatalogHost.ObserveAsync:109`); (2) `FrontComposer b3342381` (`adcc8b32`) and `Parties ca637a01` (`ea6c6fd2`) `Directory.Packages.props` overriding Builds `v6.8.5` (`Architecture.Tests` 125/126); (3) disposable `EventStore v5.6.0` (`295b5a6b`) probe committed catalog and passed `CorrectionPropagationWorkflowRuntimeShouldBeHealthyInRealDaprTopology` (61.6s), but surfaced `Memories 830484ee` tenant provisioning workflow `FAILED` and 15s/60s `HttpClient` timeouts. See [verification-20261127.json](../specs/spec-cicd/evidence/19/latest-dependencies/verification-20261127.json).
- Parked, 2026-11-27: Human approved parking until an EventStore release carrying `360ed041d` (and Builds promotion) plus upstream `FrontComposer`/`Parties` `Directory.Packages.props` delegation fixes land, then investigating the `Memories` tenant provisioning failure on the refreshed cohort. Evidence and uncommitted worktree `/home/administrator/projects/hexalith/chatbot-story-19-latest` are retained; no ChatBot commit, push, remote op, registration, or adoption occurred.

## Spec Change Log

- 2026-11-27 — Renegotiated with human approval against ChatBot `main` (`0fd555f3`, already on `net11.0`, Builds `v6.8.1`, EventStore `5.5.1+`). Updated frozen Builds pin from `v6.4.2` to `v6.8.5` (`deccbc3b`, CLI `6.8.5`), moved target SHAs to `targets-20261127.json`, and reset status to `draft` for checkpoint approval. Prior `baseline_commit` was `53857b9e4223e3a161ed0731cebbe415761f3576`.

## Review Triage Log

## Verification

**Commands:**
- `run-with-temp` standalone copy: `dotnet build Hexalith.ChatBot.slnx -c Release -warnaserror -p:UseHexalithProjectReferences=false` -- expected: 0 warnings, 0 errors.
- `run-with-temp` per-project `dotnet test` across all core suites -- expected: all pass, 0 unexpected skips (only optional manual observer unexecuted).
- `run-with-temp` with `require-runtime.py`: `Hexalith.ChatBot.Live.IntegrationTests` (`required-live.xunit.runner.json`) and `Hexalith.ChatBot.Release.Tests` -- expected: 3/3 live pass (0 skipped); 2/2 release clear owner preparation and fail at `ValidateAtomicParticipationAsync`.
- Owned-file byte/mode diff vs `0fd555f3` -- expected: 7 owned files identical; only `references/Hexalith.Builds` changed among owned items.
