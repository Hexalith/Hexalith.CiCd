---
title: '16 — Migrate Conversations'
type: 'chore'
created: '2026-11-16'
status: 'in-progress'
baseline_commit: 'd04c9ab7a8fa43dc6dac1f15d34135aba8e79551'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/specs/spec-cicd/evidence/16/planning.md'
  - '{project-root}/_bmad-output/specs/spec-cicd/evidence/16/gate-inventory.md'
  - '{project-root}/_bmad-output/specs/spec-cicd/evidence/16/shared-preparation-design.md'
  - '{project-root}/_bmad-output/specs/spec-cicd/evidence/16/windows-and-fixture-design.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Conversations' legacy pipelines include .NET 11 product checks
requiring producer-selected imports, browser/Dapr setup, an isolated fixture
and protected Windows checkout.

**Approach:** Follow AD-21 to preserve product coverage, prepare module actions,
register/render the module and let App delivery adopt it. Completion requires
green Linux/Windows CI and the next genuine scheduled nightly outcome.

**Human decisions, 2026-11-16:** Include generic shared producer preparation,
protected Windows checkout, qualification and a Builds release in story 16.
For Conversations preparation pushes before adoption only, require exact-input
package-mode builds/tests and applicable product checks, policy/commit
validation and owned byte/mode/gitlink preservation. Normal check.py remains
mandatory after adoption. This grants no owned-file edits or weaker tests/audits.

## Boundaries & Constraints

**Always:** Preserve SDK/runtime selections, product assertions and foreign
instructions/settings. Use module-agent credentials for product writes,
CiCd-agent for CiCd/Builds and command-local maintainer access for administration.
Keep Linux TestSupport coverage alongside Windows. Use run-with-temp for jobs;
retain logs outside scratch. Apply the product-only gate rule and centralize
justified waivers in a released Builds pin. Preserve concurrent onboarding.

**Never:** Directly edit module owned-perimeter files, initialize nested
submodules, manufacture producer metadata, suppress tests/audits, disable Windows
path protections, give custom actions checkout/build/environment setup, obtain
the App key, or claim adoption/nightly results from fixtures. Only delivery or
restore writes owned files. Remove legacy publication access after adoption.

## I/O & Edge-Case Matrix

| State | Expected behavior |
| --- | --- |
| Missing prerequisite or denied administrative read | Record exact failure; do not infer absence or adopt. |
| Producer imports unavailable before project evaluation | Fail; never invent an enrollment identity or defer setup to a late hook. |
| Unsafe Windows archive paths | Preserve bytes and protected checkout; module action cannot repair an earlier checkout failure. |
| Fixture catalog/lock mismatch | Deliberately qualify successor locks; retain seven product assertions. |
| Failed delivery or no releasable change | Retain authenticated per-module result; no forced release or completion claim. |

</frozen-after-approval>

## Code Map

- Context companions supply exact identities, administration, resolved gate
  dispositions, source files, APIs and failure tests. Builds/module paths below
  are relative to their respective `references/Hexalith.*` checkouts.

## Design Notes

Add nullable `moduleManifest`/`windowsCheckout`. Managed preparation binds the
accepted central catalog and truthful Platform provenance; legacy modes/hashes
stay unchanged. Separate candidate qualification binds exact product inputs,
committed render and external released Builds; production rejects its authority.
Windows uses validated outputs and protected cone sparse-index checkout with
immutable excluded-tree IDs; ordinary index expansion is unsafe.

The final fixture route uses the closed `buildProjects` alternative
`{id, project, isolatedContract}` under managed preparation. Shared code builds
the nonshipping adapter in separate SDK processes after the root solution, so
the product's Aspire SDK 13.6.5 and frozen fixture's 13.6.1 remain distinct. The
isolated SDK invocations disable node reuse, including preflight, to prevent
.NET 11's default build server from sharing resolver state. The
adapter and frozen projects stay outside the root solution; the hook runs the
seven built assertions. Existing finite-version cases keep their restrictions.
Managed catalog evaluation must preserve the exact producer inventory by
evaluating unseeded consumers without rewriting its snapshot; legacy cache
behavior remains unchanged. Both owner changes are published in v6.2.0;
Conversations' released-input qualification remains mandatory.

## Tasks & Acceptance

**Execution:**

- [x] `evidence/16/` — record human decisions, source/preflight investigation,
  gate inventory, shared design and native Windows feasibility probes.
- [x] `evidence/16/` — verify/provision AD-21 preconditions in order, preserving
  existing access until adoption and recording exact readbacks/access failures.
- [x] Builds `schemas/`, `Github/lib/module_preparation.py`, producer/CLI,
  orchestration and `Github/prepare/` — implement companion contracts and tests
  for managed/candidate authority, one preparation lifetime and protected checkout.
- [x] Architecture spine, `setup/README.md`, `templates/.github/workflows/ci.yml.j2`
  — document/export validated inputs and active catalog authority. Qualify defaults,
  CI/local/Windows/release parity; publish an acceptable Builds/CLI release.
- [x] Module `.config/dotnet-tools.json`, Platform gitlink, inventory-listed tests,
  root npm files and `.githooks/commit-msg` — update released prerequisites,
  extract product assertions and retire forbidden tooling.
  Remove active waivers; externally clear fixture demotions while preserving its
  historical source. Justified waivers belong only in released Builds `Props/`.
- [x] Module `.github/actions/{after-unit-tests,testsupport-windows}/action.yml`,
  `tests/compatibility/MinimalModule/`, package scripts and root `.slnx` — wire
  fixture adapter/seven tests, five-package payload/symbol/consumer checks and
  built Windows tests. Qualify package locks and protected product-preparation pushes.
- [x] `builds-version`, `setup/Hexalith.Conversations.yml`, `rendered/` and
  Conversations gitlink — commit released prerequisites and registration/render
  together. Enable browsers, Dapr, Admin.Web.Tests in stage 4, the fixture hook,
  Windows job, C# analysis and the direct Platform identity dependency.
- [ ] `evidence/16/` — authenticate adoption/preservation; immediately enable
  immutable releases and retire verified legacy access. Observe green CI,
  normal checker and scheduled night.

**Acceptance Criteria:**

- Given prerequisites and live actions, when delivery adopts Conversations, then
  its owned tree matches the perimeter and retained product checks execute.
- Given missing, stale or candidate-only authority, when a production entry point
  prepares a build, then it fails before evaluation; accepted central catalog bumps
  remain compatible with separately verified Platform provenance.
- Given validated CI outputs, when Windows runs, then shared prepare builds
  safely without environment setup and descendant-cleanup tests pass;
  Linux-specific tests also remain covered.
- Given the selected catalog, when the adapter builds, then isolated locks and
  all seven assertions pass; frozen fixture projects stay outside root .slnx.
- Given green adopted CI, when its next scheduled nightly completes, then CodeQL
  and publication or a valid nothing-to-release outcome establish CAP-16.

## Implementation Notes

- All changes are isolated in `/home/administrator/projects/hexalith/cicd-story-16`.
  The original workspace's concurrent onboarding work is preserved. No product
  push, release publication, remote administration, registration or adoption was
  performed during this local implementation phase.
- Builds now implements nullable manifest/protected-checkout inputs, validated
  caller outputs, managed and explicitly separate candidate producer commands,
  truthful Platform provenance versus the actual active catalog, and one verified
  preparation lifetime across CI, local checking, Windows and release source.
  Managed results admit only status/outcome/diagnostics/buildPreparation before
  exporting the seven verified values. Legacy absent-authority hashes remain
  unchanged. Normal Git HTTPS origins and native Windows root spellings are
  normalized without accepting credentials, alternate origins or reparse roots.
- Protected Windows bootstrap keeps NTFS protection and the complete logical
  tree in cone sparse-index form, binds omitted archive trees, validates the
  materialized complement, fetches complete source ancestry and initializes
  only explicit direct identities. It never invokes the parent submodule helper.
- The managed-only `HexalithIsolatedBuildContract` / `hexalith.isolated-build.v1`
  interface admits a nonshipping build-order graph with authenticated source
  roots, exact globals, locked restore, the actual catalog and preserved audited
  release targets. SDK-generated NuGet imports/assets must match an independent
  private locked restore. Arbitrary obj imports, SDK policy namespaces and
  additional properties remain refused. Setup/architecture notes document it.
- Module source retires the inventoried nonproduct gates, extracts the retained
  runtime/API assertions, adds both product actions, and validates five built
  package/symbol pairs plus isolated consumers. The non-test adapter and frozen
  fixture remain outside the root solution; the declared isolated build route
  builds their graph separately. Historical fixture projects and original locks
  are unchanged; external successor locks were deliberately qualified.
- Root npm files are preserved byte-for-byte during preparation. App delivery
  removes owned semantic-release/commitlint selectors first; a post-adoption
  product cleanup may then remove remaining npm files after selector absence and
  normal checker success. No owned-JSON qualification exception was added.
- Candidate orchestration binds the canonical perimeter, exact committed inputs,
  real released-tool provenance and a source-bound receipt. Local Dapr setup
  binds the verified executable/private runtime and labels owned resources;
  occupied user control planes refuse before mutation, and cleanup preserves
  foreign or ownership-replaced resources. No released-tool substitute exists.
- The story remains in progress. Published prerequisites, live qualification,
  adoption and scheduled-night acceptance are pending. The later explicit user
  instruction authorizes publishing and merging source changes; it does not waive
  product qualification or adoption gates. See the
  [implementation handoff](../specs/spec-cicd/evidence/16/implementation-and-verification.md)
  and [publication packet](../specs/spec-cicd/evidence/16/push-20261116T193523Z/README.md).

- Resumed administration on 2026-11-16 verified Conversations in the existing
  App installation, deleted all 296 inventoried legacy CodeQL analyses with
  acknowledged responses, provisioned/read back the exact rulesets and main-only
  release environment, added scoped NuGet policy 27245 and an isolated Zot push
  identity, and additively granted the shared pull pair and NuGet variable.
  Existing installation selections, policy 18928, registry entries and legacy
  access were preserved. Immutable releases remain off until authenticated
  adoption. The exact terminal CodeQL response was HTTP 404 `no analysis found`,
  accompanied by successful metadata reads and the deletion receipts.
- The stale consumer-declaration audit that blocked Builds CI was refreshed
  through its existing generator for seven affected families. All 317 selected
  versions and 150 other families stayed unchanged. Production audit validation,
  113 generator cases, 109 validator cases and owning root commitlint passed.
  The audit-only fix is published on Builds main at
  `fa6dc2864ac65c6244b111fa9ecc5e7a78722e3e`; exact-source CI is run
  `43951398012`. An acceptable supporting release is still required.
- Source triage also closed the approved preparation contract's unsafe scratch
  spelling gap: traversal/control-character paths now refuse before tag fetching,
  tool execution or output creation. Commit
  `27e8fba9736a4825d44c40c638c5e6f9b65ab81e` preserves concurrent catalog/audit
  work and has current CI run `43956522607`. All 152 finalized Python controls
  passed without skips; the eleven preparation cases also passed on Python
  3.12.13. Existing security findings remain under triage, with no suppressed
  checks or claimed external-gate clearance.
- Product preparation was reapplied locally onto fresh Conversations main
  `f1a2b3da468760d4188f604045deb098af8ead52` and committed as
  `47e8dde1600b7a72b86532e22644dca5d952a4ff`, with owning commitlint validation.
  The newly encountered historical measurement-envelope gate is classified in
  the central gate inventory and retired. Git identities preserve runtime
  source, the real warm-path benchmark/live projection suite, original fixture
  and named owned paths. This candidate is unpushed and has no released-input
  execution claim. See the [resumed receipts](../specs/spec-cicd/evidence/16/resume-20261116/README.md).


- Operational prerequisite follow-up on 2026-11-17 preserves the frozen intent
  and baseline: Builds `66fc4855a6d3746fbfc8ad02db27d4ecd44dd8c9` corrects
  ordered default-property evaluation while preserving current `8.0.1`, retained
  `7.0.7`, incoming literal/scope guards and all original closure/provenance
  assertions. Actual SDK ordering cases, both complete affected classes (77
  cases), strict Release builds and owning commit policy passed. New incoming
  workflow-lint findings still hold the acceptable supporting release.
- Standard nightly `43969951043` dispatched no target after a changing paginated
  delivery inventory refused completeness. The scoped controller repair keeps
  the general reader fail-closed, retries only typed count inconsistency by
  discarding the whole five-status scan, and retains the existing poll interval,
  30-minute deadline and dispatch reserve. Malformed/authentication/other errors
  stay fatal. This owning-source prerequisite repair grants no product adoption
  or nightly acceptance and does not change the frozen migration requirements.

- Pre-adoption qualification now accepts the CiCd owner read token only through a
  bounded stdin envelope from token-free ancestors. Inherited GitHub credential
  aliases refuse after scrubbing; only the mandatory global-owner-check child
  receives the token. Product/protocol/build/hook children inherit none. Before
  disposable cleanup, successful Linux qualification retains bounded exact
  TestSupport binaries, committed signed-evidence inputs, the authentic historical
  Git object and released support sources with identity/SDK/file-hash binding.
  Retention grants no native Windows execution or adoption result; those checks
  remain pending and mandatory.

- The owning runtime follow-up is published on Builds main as
  `0ccd12af6576a3aac601340dec7dba53e86768c3`: managed catalog reads preserve
  producer bytes, and closed isolated declarations use independent SDK processes
  with node reuse disabled. Strict SDK integration passed all 49 selected cases;
  the full Python suites passed 764 cases each on 3.12 and 3.14, without skips.
  Owning commit policy, package signatures and API compatibility passed. Exact
  hosted CI run `44021561686` passed all eight required jobs. Sonar analysis
  retained the baseline's 21 existing findings and identical gate ratings; no
  new issue or new reachability regression was identified. Its external failure
  is recorded separately from workflow qualification. Standard central nightly
  `44025970850` dispatched exact Builds release run `44026029259`, which passed
  its processed CodeQL security gate and reported `published` for v6.2.0 from
  `0ccd12af`. The public immutable bot release and matching public CLI Nuspec
  provenance were verified. Full Conversations qualification remains pending.
- Focused execution with the actual public 6.1.0 producer passed strict product
  restore, independent adapter restore/build, all seven fixture assertions and
  three overlay checks. Its exact producer inventory check correctly failed on
  the catalog mutation. That focused evidence is not full qualification and does
  not grant product publication, native Windows acceptance or adoption.

- Follow-up qualification fixes preserve the frozen intent and baseline. The
  portable verifier now distinguishes authored SDK declarations from reconciled
  references while validating both closures; its positive live SDK and 18 refusal
  controls passed on clean product `4239b6188a82608784f726b35a802784a1da0b4d`.
  Six other unit projects passed 2,669 cases. A proven external-container reaping
  defect was corrected with Docker init; the unchanged full Linux TestSupport DLL
  then passed 44/44. The actual public producer and all frozen artifacts remain
  unchanged. The user explicitly approved the scoped five-member v4 successor;
  product `c0767f61c3be3a5f92b5e2426dd9d801a2ca0b17` records that approval,
  retains v1/v2/v3/review bytes and adds 53 exact-scope control cases. Whole
  released-input execution on these final inputs remains required. NuGet
  authenticated readback as `jpiquot` verifies policies 18928/27245 and cleanup
  readiness. See the [compact follow-up receipt](../specs/spec-cicd/evidence/16/resume-20261116/released-input-followup.json).

- 2026-11-18 follow-up: hosted adopted CI failed at managed preparation because
  later submodule updates moved Platform from released `v2.1.10`
  `215ae18c972e6ea8ccb27032dfc11a57b098f047` to untagged
  `4f88df0ec98885425db5ddb20a3a3bb34a93d046`. Product
  `94f3d77e37c238f1eb148885951c6829c3d238d2` restores the released identity
  without owned-file edits. Standalone `python3 references/Hexalith.Builds/check.py`
  passed stages 1–3 on that commit. Immutable releases read back enabled.
  Hosted Linux/Windows CI, legacy NuGet 18928 retirement, npm cleanup and the
  next scheduled night remain. See
  [adopted-platform-pin-20261118.json](../specs/spec-cicd/evidence/16/adopted-platform-pin-20261118.json).

## Spec Change Log

- 2026-11-16 follow-up: the user requested "fix" after the publication report.
  Resume the approved remaining release, qualification and adoption work to fix
  the missing-config checker blocker. The prior explicit instruction to push all
  changes to main and merge remains in force as qualification gates permit.
  No owned-module edit, fabricated receipt, skipped test or audit weakening is
  authorized. Continue from the existing isolated worktree and full baseline.
- 2026-11-18 follow-up: restore the released Platform pin after adopted CI
  refused untagged Platform main during managed preparation. Immutable releases
  are enabled. Hosted CI, legacy NuGet retirement and scheduled-night acceptance
  remain required.


## Review Triage Log

## Verification

Performed local source qualification (all disposable work used `run-with-temp`):

- Strict SDK 11 build: zero warnings/errors; privately pack/install/invoke both
  new commands. Twelve new producer/authority/isolation cases and 138 selected
  legacy producer/root/Platform cases passed with zero skips.
- Actual producer-selected adapter restore/build with shared release audit
  targets passed; all seven fixture assertions and all three overlay assertions
  passed. Changed generated policy imports and restored assets graphs refused.
- Conformance, Portable and TestSupport product test projects compiled strictly
  with zero warnings/errors; the projection-key case and twenty retained portable
  API/dependency/artifact assertions passed.
- Five package/symbol pairs passed payload validation; fresh package-only public
  and testing consumers restored, built and ran successfully.
- Native Windows protected sparse-index qualification passed. The complete
  unfiltered built TestSupport DLL passed on native Windows: 44 tests, zero
  failures/skips/not-run, using exact .NET 11.0.0 installed only in private NTFS
  scratch and verified against Microsoft's published SHA-512. Existing machine
  runtimes and the user's Dapr containers were preserved.
- Python 3.12.13 and 3.14.4 each passed 233 cases across thirteen standalone
  groups, including ten preparation controls, ten protected-checkout/history
  controls and seven Dapr ownership/cleanup controls. Offline renderer (33) and
  validator (51) suites, render reproducibility and the qualification lock check
  passed. The broad Workspace run did not pass (HXR021 failures, three contextual
  skips, terminated after twenty minutes); causality remains unverified and it
  contributes no passing coverage.

Exact commands, retained logs and final counts are in
`evidence/16/implementation-and-verification.md` and `verification-results.json`.
The source-only private tool version is not a published release or production pin.

Still pending, and **not** claimed as performed acceptance:

- AD-21 administrative preflight/provisioning, acceptable published Builds/CLI
  release, real module tool/Platform prerequisites and protected preparation push.
- Committed registration/render against that release, full `tools/validate.py`
  live-module qualification, App delivery and authenticated preservation.
- Genuine released-input Linux/browser/Dapr/AppHost and full module Windows CI,
  adopted normal `python3 references/Hexalith.Builds/check.py`, immutable release
  readback, legacy access retirement and the next scheduled nightly outcome.
- Genuine local Dapr integration also needs an unused host control plane; this
  workspace has four existing user Dapr containers and correctly refused setup.
