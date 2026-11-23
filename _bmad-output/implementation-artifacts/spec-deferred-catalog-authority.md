---
title: 'Resolve five deferred catalog authority findings'
type: 'bugfix'
created: '2026-11-23'
status: 'done'
route: 'oneshot'
---

<frozen-after-approval reason="human-owned intent">

## Intent

**Problem.** Builds can reuse a recorded package view for a differently cased project name, and runtime inventory omits historical catalog selectors written with `MSBuildProjectName.Equals`. Three related findings still need a decision based on current source.

**Approach.** Resolve DW-27 through DW-31 as one catalog authority batch. Preserve exact consumer identity during catalog evaluation, snapshot validation and package lookup. Have Python inventory discover literal `Equals` selectors while preserving selector spelling. Verify the upstream default catalog lookup and current toolchain pins, and confirm whether the historical retained selections still need audit records. Record the results in CiCd's deferred-work ledger.

</frozen-after-approval>

## Implementation Notes

- Builds base `443c48bb497ec45f6fc1ac3f30e25860d1eb3fed`. Materialization, composition reads and build validation now use exact project names. Each batch wrapper has a separate directory so names that differ by case can coexist on Windows. Package IDs still match case-insensitively. Snapshot hashing retains its original sort for names that differ by more than case.
- Python inventory discovers literal `MSBuildProjectName.Equals` conditions in preprocessed imports and evaluates the exact consumer name. The regression uses MSBuild to select the retained view and a differently cased consumer to check the default view.
- Builds `0a1d2e028c554798969643485631eab245ef020d` and `66fc4855a6d3746fbfc8ad02db27d4ecd44dd8c9` corrected DW-28's default property lookup to follow unconditional and empty-value defaults in source order. Builds `2c33b2d749a2f7b8c67a15130a815996f83a51a5` made the runtime and probe use the current catalog for DW-30. Its remaining frozen Dapr SDK assertion now checks the v1 literal.
- Builds `286ed438367e9dbb9a0a0ab65a1538f8806bf191` retired the remaining SDK 4.2 compatibility selectors. Current named conditions affect package inclusion. The four current versions have listed audit rows that match the committed catalog bytes.

## Review Triage Log

- Medium, patched. Discovery matches candidate names without regard to case and uses their actual spelling for MSBuild, which applies the different semantics of `==` and `.Equals`.
- Medium, patched. Literal selectors and evaluation wrappers support project names with leading underscores and spaces. The inventory test exercises both with real MSBuild.
- Medium, partially patched and deferred. Preprocessing now uses package mode, matching evaluation. Imports gated on the consumer name can still be absent during discovery.
- Medium, deferred. The no-snapshot property lookup resolves the DW-28 version fallback, while a separate conditional `PackageVersion` inclusion still requires a default-view evaluation design.
- Low, patched. The deferred-work ledger records the five dispositions.
- Low, patched. The verification record identifies the exact committed catalog and audit blobs used for DW-31.

## Verification

- Builds `main` was verified at `641dd5e47ced09389ae0698d9eee34befcc45a5c`, tree `49c467450a0220d3597f3d3cfb3505b09358f89d`. The Release build of `Hexalith.Builds.Module.Tests.csproj` completed with zero errors and warnings on .NET 11.0.100. The committed NuGet signer configuration was used with local offline certificate revocation checking. Build log SHA-256 `44821d12e1766b0e258f243bd9b4593693b65313b8f7bc9d59d300ab6d16448a`.
- All 144 focused .NET tests passed across `CatalogVersionTests`, `CompositionCatalogPackageViewTests`, `SupportedPlatformPinsCatalogTests` and `CompositionPrerequisiteProbeTests`. The test harness selected the pinned SDK with workspace-local runtime and cache directories for isolated SDK children. Test log SHA-256 `68b2da0b084abc83af7733de52cd062dd635172319b25e797074220dea977d2d`.
- `python3 Tools/test_evaluated_catalog_modes.py -v` passed all three tests using .NET SDK 11.0.100. The inventory regression failed on the unchanged Builds base because inventory selected the default for the retained consumers. Candidate log SHA-256 `9bcdab68bf470bbdff2edb62ffb4db593125eaf1f2127aea73027c221dbbb6b9`.
- The DW-31 probe compared the four unconditional package pins with the current audit rows and verified the raw and normalized catalog digests. Catalog blob `2a725fc2837a5a4a35f90da0581503dd4bf11ceb` matches the audited revision `88face124900de97c248f027e1caedda9341c786`. Audit blob `2d5e356c3e189b0bbf814eedc4259a76f96fba0f`. Probe output SHA-256 `a73a164c3ab06b13f2202070e82e05223a51b7b30152c0e5dad0d41298f00430`.
- `pwsh -NoProfile -NonInteractive -File Tools/validate-package-version-audit.ps1` returned seven identical errors on the candidate and the clean Builds base. The earlier release-records change `4adecfe2af4758aa66039a1221de20774ca56e87` added an embedded schema to the audited tooling project file. Both logs have SHA-256 `b5310f3b23bc5fe6657133eafc73c1878d11cbd087fb89f1c8f99948b149cb7d`.
- All eight CiCd evidence checker tests passed. Commitlint 21.2.4 accepted both complete commit messages under the owning Builds policy and the CiCd-pinned Builds v6.6.2 policy.
