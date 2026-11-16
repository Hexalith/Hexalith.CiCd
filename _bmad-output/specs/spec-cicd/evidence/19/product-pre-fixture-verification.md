# Story 19 product blocker follow-up

Local product work only; no commit, push, administration, registration or adoption was performed by this handoff. The separate nightly prerequisite and hosted acceptance remain the parent session's responsibility.

## Exact product snapshot

Preparation base: `bf0f44ff395d89c5565a423b424e389d2f80d0f6`. Final tracked diff SHA-256: `1d498d232372a177cbcc3725193fa0bc838bc39b2f9c813d5d4c1fbbfaaad92e`. The four added files have their individual hashes in `product-fix-ownership.json` and each final verification JSON. These hashes identify the verified working snapshot; they must be matched to the eventual product commit before publication.

The seven protected whole files retain their baseline bytes and modes, all sixteen dependency gitlinks are unchanged, no nested submodule was initialized, SDK `11.0.100` is unchanged, and `LiveRecoverySweep` retains its prepared scenario body. No warning, vulnerability audit, assertion or skip condition was weakened.

## Product fixes

- Share the manifest-pinned published Tooling path and existing source/package defaults between project and solution evaluation. Local Debug keeps source mode; CI and Release keep package mode. The four existing cache selection cases retain their precedence.
- Propagate composition inputs through NuGet's restore walk and SDK-generated transitive project edges. Otherwise restore invents a Builds.Tooling source edge, and solution compilation drops some Platform descendants into Debug. The exact pinned SDK's NuGet graph input property is used; a future SDK change must requalify that path.
- Point the recovery contract at the renamed `LiveRecoverySweep` predicate, retaining the production-predicate assertions. Move the destructive recovery serialization collection into the dedicated recovery project and apply it to its entry point.
- Place the two ordinary live Aspire classes in the existing nonparallel realm-template collection. Their previous concurrent starts competed for Keycloak's fixed local port; every test and assertion remains present.
- Update the existing package-mode-default architecture assertion to read the shared imported props where that unchanged default now lives.

## Verification

`verify-product.py` creates private repository/source snapshots, package feeds and outputs beneath `run-with-temp`'s `TMPDIR`, using only locally available Git objects at ChatBot's exact gitlinks. Canonical global root mappings avoid duplicate paths. The layout is acyclic. Build, test, package and evaluation commands have timeouts and wait for child completion; a zero test-runner exit without a completed passing summary is rejected.

Reproduce from this worktree:

```bash
run-with-temp python3 _bmad-output/specs/spec-cicd/evidence/19/verify-product.py --phase evaluate --timeout 180
run-with-temp python3 _bmad-output/specs/spec-cicd/evidence/19/verify-product.py --phase packages --timeout 180
run-with-temp python3 _bmad-output/specs/spec-cicd/evidence/19/verify-product.py --phase all --live --timeout 900
```

Completed on the exact final snapshot:

- Full Release/package-mode solution compilation, including integration and recovery: zero warnings/errors. The composition assets contain no Builds.Tooling source project and agree on the selected telemetry/framework dependency closure (`product-composition-closure.json`).
- All ten complete unit suites: Architecture 119, CLI 61, Client 141, Conformance 151, Contracts 531, MCP 70, Server 3,629, Testing 41, UI 613 and Workers 32: **5,388 passed, zero failed/skipped**.
- AppHost: **18 passed**, zero failed/skipped.
- UI E2E: **289 passed**, zero failed/skipped, using the real configured Chromium browser (`product-ui-e2e-verification.json`). Together with units/AppHost, **5,695 tests completed successfully**.
- Contracts, Client and Testing package creation, followed by an isolated local-feed consumer that loads all three packages and checks contract identity round-tripping and the testing facade: passed (`product-packages-verification.json`).
- Four cold cache cases without `obj`, plus real solution/project default parity probes: passed (`product-evaluate-verification.json`).
- Dedicated recovery discovery lists exactly `Hexalith.ChatBot.Recovery.Tests.LiveContinuityAspireE2eTests.LiveRecoveryValidationRunsAllThreeCoordinatorsAndPassesEvidenceGate` (`product-recovery-discovery.json`). Discovery is not execution of the multi-hour recovery sweep.

The final required-live IntegrationTests command reached its **900-second bound, exit 124**. The run repeatedly reported absent independently bound catalog host identity/profile, rejected workload scopes, and projection activation authority failures. It has no completed green project summary. `product-all-verification.json` records this failure against the exact final hashes; the overall verification is **not green and does not authorize a push**. The command and workspace wrapper have exited, and no scratch-scoped child processes remain. Existing independently enrolled policy-refusal witness requirements remain intact; no witness is fabricated or inferred from runtime opt-in.

## Sourced product and routing gaps

`product-live-input-investigation.json` separates missing composition setup from local layout and credential issues. Both legacy workflows were read without alteration, as were their baseline build/tool resolver scripts. They supply the same published tool, package-mode selectors and live flags. Their explicit service-grant lifetime is 90 days, matching the current AppHost default. The permitted AppHost user-secrets location exists but has no catalog/profile key; only key names were inspected, with no values retained. There is no relevant ambient catalog environment setting. The required ordinary AppHost/test startup does not wire `AddEventStoreDevelopmentRouteCatalog`.

The existing `PolicyRefusalPreflightTopology.cs:346` reference prepares real compiled Tenants/Parties/Projects owner inventories and explicitly does not invent a ChatBot owner. Its call at line 377 omits custody options. At exact EventStore gitlink `77a2dafdf2e6aab7382afab7ab50e22144361d42`, `DevelopmentRouteCatalogAspireExtensions.cs:107` rejects that omission. `DevelopmentRouteCatalogCompositionOptions.cs:6` requires explicit private custody, authority component/state key, complete digest ring and active/map generations. Its `docs/reference/development-route-catalog.md:302` permits first material only with an actually new, owner-isolated business backend; the default Dapr Redis or an empty cell is not freshness proof. The public composition helpers can capture actual host observations and retain genuine custody after an owner supplies such inputs. They do not generate a replacement profile or keys. No custody material or observations were created by this handoff.

The positive M2 constraint comes from current executable code, independently of its stale Story 1.8 comment: `CommandGatewayServiceCollectionExtensions.cs:79` registers `ChatBotAdmissionEvidenceValidator`; its `ValidateAtomicParticipationAsync` at line 372 unconditionally returns `CanonicalExecutionUnavailable` for every profile. The passing Server tests retain that negative assertion. The live M2 method requires a governed command to be `Accepted` at `TrivialGovernedCommandAspireE2eTests.cs:819`. The current A13 reconciliation requires one exact owner-accepted executable atomic/audit/fencing bundle; a completed correlation/status story or reconciled document is not that bundle. Neither the guard nor the positive M2 assertion was changed.

Legacy CI selected the refusal smoke and Story 13.2 matrix; legacy release separately ran the positive M2 gate. Turning on Tier3 for the whole ordinary integration project now pulls that release-only gate into CI. A minimal proposed correction is a dedicated release-test project invoking the unchanged M2 harness, assigned through `tests.exclude` to the enabled daily nightly hook. The weekly destructive recovery project remains separate. Recovery must still run when due after M2 fails, provided prerequisites succeeded and the run was not canceled. Preserving the prior 30-minute release-gate allowance plus recovery's existing 330-minute allowance calls for a **proposed 360-minute sequential hook allowance**. **This proposal was not implemented; the frozen 330-minute decision is unchanged pending human disambiguation.** No test filter, new skip, broader credential or weakened assertion was added.

## Superseded attempts and limits

The older MSB3277 conflicts and missing Memories deployment asset were verification-layout defects: duplicate source paths restored inconsistent assets, and the snapshot lacked the tracked deployment file. Complete canonical exact-gitlink snapshots compile those unchanged sibling products successfully. No sibling product was edited and no package pruning or audit suppression was added.

The first broad scratch layout also linked all archived siblings to one another, producing cycles in a genuine recursive architecture scan. That interrupted MTP run returned zero without a summary and is not accepted as passing. A complete acyclic rerun passed; final runs use the corrected layout and require completed test summaries.

`product-transitive-inputs-before.*`, `product-recovery-compile-before.*` and `product-live-concurrency-before.*` retain superseded failures/cancellation for diagnosis. They do not certify the final snapshot. Final evidence uses `product-{all,evaluate,packages}-verification.*`, the explicit recovery-discovery result, the composition closure and ownership report.

The product checks use ChatBot's unchanged Builds gitlink `6ad5854aa14a9950e1fbfc32d7e27953a1c4b82b`. They do not certify compatibility with the future shared nightly prerequisite release. Full recovery execution, released-prerequisite verification, AD-21 preconditions, candidate validation, delivery, hosted green CI, credential cleanup and the next central nightly outcome remain outstanding. After adoption the standard local checker is mandatory.
