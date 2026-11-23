---
title: 'Resolve five deferred release verification findings'
type: 'bugfix'
created: '2026-11-23'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="requested five-item batch">

## Intent

Close five open findings from the CiCd backlog. Revalidate the correlated run
attempt before finalizing a nightly artifact read error, and keep a newer attempt
pollable even if it has already completed. Verify the shipped literal audit-waiver
guard for DW-11, the explicit endpoint and attached-routing test results for
DW-14, the hosted recovery of the Builds catalog and Evidence tests for DW-26,
and the nightly automated fast-forward push reported as unverified by story 8-2.
Record the confirmed scope of each observation in the backlog.

</frozen-after-approval>

## Implementation Notes

- CiCd investigation baseline `0e3ab54ecf9958b6986296d361c53ca52bc68e44`.
  Publication was rebased onto `d6b191f6684a1f4339bc1d7351daa5ab9f05b81d`
  after three unrelated commits landed on main.
- The wait controller rechecks the correlated run before recording a successful
  outcome or an artifact read error. An attempt or status change keeps the
  updated run pollable. Stable artifact errors remain target failures. An
  unreadable confirmation also leaves the run pollable and records an
  orchestration error outside the slice boundary. The App inventory binds the
  controller at `71fdfc75eb70be38f1a4abb40fcd5822b48fba04`, tree
  `7ec809ddffed50e40a8714dc0cf8e1372d710a76`. Its SHA-256 is
  `b200ad0ee5091bb806ac729f03a5b689eaf149eb371bc0c46d8b28ad8273d953`.
- Builds v6.6.2 resolves to `2d9ef8b454ff897daca0149f3549844f584b634a`.
  All 19 audit-lint tests passed at that source. Separate committed-Git probes
  rejected NU1903 waivers in Directory.Build.targets and PackageReference
  metadata with the offending paths. Stage 1 guard blob
  `a43a12c319150cc49cebb1996e4e883f7013b232` invokes audit lint.
  Release resolver blob `d4845a15fcc01106ff5555fdc7def3e3096c9740` requires
  green exact-source CI before create-mode publication.
- Each probe made a fresh Git commit and called
  `audit_lint.lint(expected_state.tree_snapshot(expected_state.Git(root)))`.
  Both raised `ExpectedStateError` for NoWarn suppressing NU1903.

  | Committed probe file | Input SHA-256 | Exception message SHA-256 |
  |---|---|---|
  | `Directory.Build.targets` containing a NoWarn property with `$(NoWarn);NU1903` | `40126f59d50bcb9571b199ff3d68fda288a077fc3d08bbbefda43efb1342d15c` | `97c3746117759e16b1bcaa507d8333651be7fec45e79c037250a07b6bce78216` |
  | `Consumer.csproj` containing `<PackageReference Include="Newtonsoft.Json" NoWarn="NU1903" />` | `c0ef77214e1a19587ebe152f705e67dd17bca674b3635cb4d7c07abbabea0d2b` | `aebcd0b516ec477d7dc297650df7247af931d83d3ec58b0638a12c38b9ad099f` |

- Builds revision `2dc16bba3053c1efc871a221a4e782a8c3da72ab` ran the
  unfiltered Module.Tests project and passed 3,094 tests. The named skips were
  `WorkspaceMsBuildTests.RootDeclaredEventStoreCandidatesExcludeArchivedEvidenceAsync`,
  `WorkspaceMsBuildTests.RootDeclaredCommonsLibraryCandidateSelectsSourceAsync`,
  `WorkspaceAppHostTests.PlatformPlanDelegatesToThePinnedModelAsync`, and
  `CompositionSdkProcessTests.QualificationCatalogProbeInterceptionIsEstablishedAsync`. Its
  StartupReadinessTests, NativeTestExecutorTests and SelectedRoutingCatalogSnapshotTests
  blobs are `8c983c1735d63a6987338fb29bb2bc925f22c9ab`,
  `772b91566a05d59a8f7119322e80f826da1b52ba` and
  `f07fa2cab376672b3d02c82867f6dd092b47f1ee`. The decoded job log
  SHA-256 is `0158608b67f9c7d1345663d527924e4e067e66957f04de5cdb734bc84e6bde5f`.
  This observation covers the existing test cases. A local replay using
  `dotnet restore --configfile NuGet.ci.Config` on SDK 11.0.100 stopped at
  NU3018 because certificate revocation servers were unreachable. [Hosted .NET job](https://github.com/Hexalith/Hexalith.Builds/actions/runs/43519435001/job/132209687921)
- The original catalog and Evidence.Tests follow-up ran at Builds
  `185e3a4e695f392e114eacffbdecd2a23da32c9b`. The committed verification
  receipt blob `061ea4e1e09cab7cf822b29164488f95b4235cd7` records that
  all 191 Evidence.Tests passed and the historical exception was unused.
  [Hosted run](https://github.com/Hexalith/Hexalith.Builds/actions/runs/43440467144) · [Receipt](https://github.com/Hexalith/Hexalith.Builds/blob/4dffd595e54699320d483edc1f27aff9b62ed8ca/docs/cicd-5-1-guard-drift-check-verification.json)
- CiCd scheduled run 44715684274, attempt 1, used source
  `8c83d4b2b5217a19180fb42fd3960b3c7d6506f0` and nightly workflow blob
  `03e4599a0409d86ea10733cbd2bb17ea02a68391`. The job token fast-forwarded
  main to `634fe40ef3f0f1e8aba55251ed8ca574db41fc1d`, with that source
  as its sole parent. Artifact 14621812680 (`hexalith-nightly-bump-push-1`) has digest
  `sha256:3bb37c5d69774d0555284b74adb7d6a39f910ff57a846bd9c0ed50347a70bdc1`.
  No idle-branch keepalive write was observed. [Hosted bump-push job](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/44715684274/job/136236963286)

## Review Triage Log

- Medium, fixed. An unavailable status confirmation made the original attempt
  terminal. Retain the diagnostic and let polling confirm a later response.
- Low, fixed. Record the two audit probes, their inputs, and their diagnostic
  digests. Attribute the release requirement to resolver source inspection.
- Low, fixed in the retained evidence. Identify the four module-suite skips
  and the exact blobs of the relevant classes. The available hosted run is
  unfiltered and has no retained per-case report. Local restore failed before
  a filtered run could start.
- Low, fixed. Link the catalog and Evidence verification receipt at the
  revision that contains the recorded blob.
- Low, fixed. Record the bump receipt artifact ID and name.

## Verification

- All 50 nightly controller tests passed in four shards. The six rerun
  scenarios included two transient HTTP 404 responses on the status
  confirmation. A replay of the original four-scenario test
  against the baseline reproduced three failures.
- The locked suites passed 40 nightly runtime, 30 nightly workflow and 52
  renderer tests. The renderer found no drift. After the rebase, 21 App
  inventory, 78 validation and eight evidence checker tests passed. The final
  App inventory check covered seven workflows, ten jobs and 76 token requests.
- Builds v6.6.2 commitlint CLI 21.2.4 accepted both complete commit messages.
  The message digests are
  `f11a739cd60da9baa864eff089f10a1697d32cfd360555764dabc6b700de6cd9` and
  `76dc559a03c9161ceccc000cbb9dbe0406966305eb603ede95a8fe819c2b1278`.
