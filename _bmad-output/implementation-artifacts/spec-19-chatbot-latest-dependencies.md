---
title: '19 follow-up: Move ChatBot to latest dependencies'
type: 'chore'
created: '2026-11-18'
status: 'in-progress'
route: 'dispatch'
review_loop_iteration: 0
context: []
baseline_commit: '53857b9e4223e3a161ed0731cebbe415761f3576'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** ChatBot's required live and release cases fail in the pinned EventStore 4 owner loader, which refuses the host's app-local System.Text.Json. Its Hexalith dependencies also lag the net11.0 releases that the shared catalog now provides. This blocks story 19.

**Approach:** Human decision, 2026-11-18 ("yes move to latest"): move ChatBot to net11.0 and the latest Hexalith dependency releases through the shared catalog. First prove, with one required live case, that the EventStore 5 loader admits ChatBot's owner children.

## Boundaries & Constraints

**Always:** Do ChatBot product work from current ChatBot main, and make writes only with module-agent. Keep SDK 11.0.100. Keep every test and assertion. Change only expectations that encode the target framework itself. Keep story 19's topology exception: gitlink-pinned AppHost executable/composition sources, with library references in package mode. Use the shared catalog's versions and override a Hexalith version property only when a dependency minimum or the loader's byte-identity rule requires it. Any push follows story 19's pre-adoption verification exception, freshly rerun for the exact candidate.

**Never:** Edit ChatBot's other CiCd-owned files: workflows, `.claude/settings.json`, instruction blocks and Dependabot. Never copy framework DLLs or weaken loader, authentication or admission guards. Never skip or filter tests. Never change sibling repositories or initialize nested submodules in the umbrella checkout. Never register or adopt ChatBot.

**Human decisions, 2026-11-18:**

- Builds gitlink: approve a one-time pre-adoption move of ChatBot's `references/Hexalith.Builds` to the exact commit of CiCd's `builds-version`, v6.3.1 (`db7bb7179244ce33483231687486381305c7c3db`). This amends story 19's ownership check for this one gitlink only; every other owned file and gitlink section stays byte-identical. Local overrides that duplicate the catalog are rejected.
- Atomic participation and the positive M2/origin release cases are out of scope. They stay ChatBot Story 1.8's work and need an EventStore owner-transaction capability that no release up to v5.3.1 provides. Both cases remain honest release blockers; do not change, filter or reroute them.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Loader proof passes | net11 host and Tenants owner child on EventStore 5.3.x | One required live case gets past owner preparation | Continue the full move |
| Loader still refuses | Same | Record the exact refusal and stop before the full move | No workaround; report it |
| Latest tag still net10 | Parties or Projects as an AppHost source | Pin the newest net11 `main` commit; package references use the catalog default | Record the exact commit |
| Required refusal cases | Atomic participation still refuses | All three required live cases pass, zero skipped | Fix the product; keep assertions |
| Positive M2/origin release cases | Atomic participation still refuses | Both run and fail at admission, no longer at the loader | Record the result; it is not a story failure |

</frozen-after-approval>

## Code Map

- `../../../chatbot-story-19-latest` (absolute `/home/administrator/projects/hexalith/chatbot-story-19-latest`), branch `story/19-chatbot-latest-dependencies` at `ddd385ec6b37a7bb6362cdc66cb3a1a0def935d3`, which was ChatBot remote main on 2026-11-18 -- the only place to commit ChatBot product changes. Leave `references/Hexalith.ChatBot` in the CiCd checkout untouched. Build and test in standalone copies under `run-with-temp`. This phase does no fetch and no push.
- [latest-dependencies-plan.json](../specs/spec-cicd/evidence/19/latest-dependencies-plan.json) -- exact base, pins, targets, catalog defaults, the loader mechanism and the atomic-participation findings. Read it first.
- ChatBot `references/*` gitlinks; `src/Hexalith.ChatBot.AppHost/Hexalith.ChatBot.AppHost.csproj:35-49` -- AppHost source composition: EventStore, Tenants, Platform, Memories, Parties, Projects.
- ChatBot `Directory.Packages.props:7` -- imports the Builds catalog; version properties set before it override the catalog defaults.
- ChatBot `Directory.Build.props:24` (net10.0), `Directory.Build.targets:22` (`aspnet:10.0-alpine`), `eng/ChatBot.Composition.props:19` (`tools/net10.0/any`), `.config/dotnet-tools.json:6` (Builds tool 4.48.2) -- runtime and tooling targets.
- ChatBot `tests/Hexalith.ChatBot.Architecture.Tests/ScaffoldArchitectureTests.cs:1099` (asserts net10.0) and `MemoriesProbeCommandGateway.cs:191` (`net10.0` output path) -- framework-encoding expectations.
- EventStore v5.3.1 `src/Hexalith.EventStore.Aspire/DevelopmentRouteCatalog{OwnerLoadContext,RuntimeSnapshot,OwnerPreparationExtensions}.cs` -- loader behavior; read-only.
- Keep unchanged: ChatBot `ChatBotAdmissionEvidenceValidator.cs:372-379`, the evidence source DI, and the recovery and M2 scenario bodies.
- Story 19 [code investigation](../specs/spec-cicd/evidence/19/code-investigation.md) and [fix verification](../specs/spec-cicd/evidence/19/product-fix-verification.md) -- live-fixture custody, the backend and the 6,243-test baseline.

## Tasks & Acceptance

**Execution:**
- [x] ChatBot (standalone copy under `run-with-temp`) -- loader proof: retarget the test host and a Tenants v8.0.2 owner child to net11.0 on EventStore 5.3.x, then run `GovernedCommandsShouldFailClosedWithoutAtomicParticipationInRealDaprTopology` -- settles the unverified loader claim before the full move.
- [ ] ChatBot `references/*` gitlinks -- move each one to its plan target, and Builds to v6.3.1 `db7bb7179244ce33483231687486381305c7c3db` -- the latest net11 sources and catalog.
- [ ] ChatBot `Directory.{Build.props,Build.targets,Packages.props}`, `eng/ChatBot.Composition.props`, `.config/dotnet-tools.json` -- net11.0, `aspnet:11.0` base image, the matching Builds tool, and catalog overrides only where required.
- [ ] ChatBot `src/`, `tests/` -- adapt to the Aspire 17, Commons 3, Tenants 8, Memories 4 and FrontComposer 6 APIs and to the framework-encoding expectations, with zero warnings.
- [ ] `_bmad-output/specs/spec-cicd/evidence/19/latest-dependencies/` -- record the exact revisions, the owned-content comparison and the results with digests. Raw logs stay under `$TMPDIR`.

**Acceptance Criteria:**
- Given the moved ChatBot, when built in package-mode Release, then there are zero warnings and errors, and the unit, AppHost, integration and UI E2E suites pass with no test lost from the 6,243 baseline.
- Given the moved ChatBot, when compared with its base, then the owned files are byte- and mode-identical, and only the decided Builds gitlink changes.

## Implementation Notes

- Loader proof, 2026-11-18: The proof did not pass, so work stopped before the full move (I/O matrix row 2). ChatBot HEAD is still `ddd385ec6b37a7bb6362cdc66cb3a1a0def935d3`. The proof inputs remain uncommitted in the ChatBot worktree as tree `bd05c98f217f95d6388f48d041a9576a1e7348f1`. With them, the package-mode Release solution builds with 0 warnings and 0 errors. The required case then fails during owner preparation.
  - The EventStore 5.3.0 loader no longer refuses System.Text.Json. The Tenants v8.0.2 net11 owner is prepared with 24 declarations.
  - The Parties child loads with host-identical SDK bytes. It is then refused with "No compiled owner declaration source was enrolled", because Parties main enables its catalog API only for EventStore up to 5.1.1.
  - Without the byte-identity override, the Tenants child (local 5.3.1 pin) is refused against the host's 5.3.0.
- Three human decisions are open:
  1. Parties needs a release that qualifies the EventStore 5.3.x catalog API. Tenants v8.0.2 accepts only 5.3.0 or 5.3.1.
  2. Plan target Projects `69697a08` does not compile in package mode, because it uses Conversations APIs that no release provides. The proof used `146d0f7e`.
  3. Builds v6.3.1 pins Aspire 13.6.5. The base AppHost SDK 17.0.0 then fails restore with NU1109, so the proof used SDK 13.6.5. Aspire 17 needs Builds v6.3.2.
- Owned files are byte- and mode-identical. Only the Builds gitlink changed. No commit, fetch, push, registration or adoption occurred. See [loader proof](../specs/spec-cicd/evidence/19/latest-dependencies/loader-proof.json).

## Verification

**Commands:**
- `run-with-temp dotnet build Hexalith.ChatBot.slnx -c Release` in a standalone package-mode copy -- expected: 0 warnings, 0 errors.
- `run-with-temp dotnet test` per test project, with the required-live runner config -- expected: all pass; the only unexecuted case is the optional manual observer.
