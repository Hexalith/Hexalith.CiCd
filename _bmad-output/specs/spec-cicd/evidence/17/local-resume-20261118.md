# Story 17 local qualification, 2026-11-18

Story 17 remains in progress. The step-03 scope covers local preparation and verification. The predecessor checkpoints, live AD-21 work, production registration, adoption, credential retirement, green delivered CI and Folders' own nightly outcome remain pending.

## Tested source

- CiCd `dc931eafa9f50c68f847650ea0d7aa60c8bfce0e` selects Builds `v6.3.1`, peeled commit `db7bb7179244ce33483231687486381305c7c3db`. The umbrella Builds checkout is at `6b6eb4eec1b9c718e4d3581fdcbe77f8b09907f1`. [The saved nightly Builds release outcome](../11/scheduled-20261118-Hexalith.Builds-outcome.json) identifies the release commit.
- Umbrella Folders `97e04cafb4c2e11bbe4cfbd6d50856b940cd7376`, tree `aedda19b785641ee5030f8f14343625c592e02a3`. The later standalone cached `origin/main` is `a53fcb940fa1114fe3ead0af2775af388e39432c`, tree `543f7fde9adfb9feffb165214d12f16fd390e5b9`. The later commit changes only 12 direct gitlinks. Publication requires a fresh read of remote main.

| Direct dependency | Umbrella Folders pin | Standalone cached main pin |
| --- | --- | --- |
| Builds | `f01f4d8401609cad9cf283e26c95a807059484f1` | `08dc4d275c7fc55c30b6b77bbdae0f36d3884090` |
| McpCli | `bd52bcd84382de7ff7819d682ee6a265d1c03b56` | `ac34ea908d2817738a174d4b47c6fbdcac898efa` |
| Memories | `4aa7f59bea22281672a916c6043e10e61eaa69f2` | `4aa7f59bea22281672a916c6043e10e61eaa69f2` |
| Platform | `3637de4afd1359b966f31946fafcac2bb0c63400` | `a8e7c867895c2f542bc2719a8e302f45621a4d25` |
| Tenants | `40d3de705a48bd01ab3a22b6511c0f9e3a11d854` | `929bac5a9881213b05ddeefc0e2ebd5b0327d819` |

## Package build and hooks

The exact umbrella Folders restore failed with `NU1009`. Aspire AppHost SDK 17 implicitly adds `Aspire.Hosting.AppHost` when the project omits it. Both pinned Builds catalogs already declare 17.0.0 for that package. Add a versionless `PackageReference` for `Aspire.Hosting.AppHost` immediately before the existing Redis reference in `src/Hexalith.Folders.AppHost/Hexalith.Folders.AppHost.csproj`. This gives central package management the explicit reference and leaves the SDK, targets, and audit settings intact. The original product blob is `9becb32297f354273ad6b77f0cf6d332937604fe` in both snapshots. The resulting blob is `d272dc002db3b1cf47e0909b2025b0182166e846`. The tested umbrella candidate tree is `696af3eba7cd88fe2b6eee0dd4f1532db68ce2d7`.

The package commands used `.NET 11.0.100` and `Hexalith.Folders.CI.slnx` with `-p:Configuration=Release -p:UseHexalithProjectReferences=false -p:NuGetAudit=true -p:NuGetAuditMode=all -p:NuGetAuditLevel=low -warnaserror -m:1`. The build used `--no-restore` after the audited restore. Complete suites used the checked-in hook runner and its existing strict counters. Clones came from local Git objects under `run-with-temp`.

| Check | Result | Output SHA-256 |
| --- | --- | --- |
| Original audited restore | Exit 1, `NU1009` | `36b0cef63f4047b079218272d97f0643ac36b98d065d0d513b8d1b6979696709` |
| Candidate audited restore | Exit 0 | `3735c4273998ef0ff2751ab7c941a228734dc778278a28ab16b8a92825595294` |
| Candidate audited Release build | Exit 0, 21 existing obsolescence warnings, zero errors | `755b5b900380db5ea5603fcf18e1b6e741459b97927410f6b973af54d23be00e` |
| Complete Contracts | Exit 0, 493 cases, zero unsuccessful counters | `16ce6d42e6c34914e6c426143e06f30a6d7503c1473aa00ac82199af1464b7c8` |
| Complete Client | Exit 0, 392 cases, zero unsuccessful counters | `098212ca40acf14267deffd06b899e4a379bd1d021b155b9f3be9398ac80ae56` |
| Complete UI.E2E with accessibility | Exit 0, 63 cases, zero unsuccessful counters | `0fc217f39e4844d464cb1f8a401bdc15d1a1e81499e85888f86017684a5f1394` |
| Complete core provider project | Exit 1, strict rejection of two skipped cases out of 2,489 | `c03e5c3661d92f878606f00f33a7fe77359c9eca863569dd7267d2fb66b4f58c` |
| Server without prepared fixture | Exit 1, Platform launcher required a Maven-built provider before running any case | `71d06613b1bd21708387476c1e1210e65b101ae5235e63f224c8950403df8409` |
| Disposable Keycloak provider build | Exit 0, `mvn --batch-mode --no-transfer-progress -f references/Hexalith.Platform/infrastructure/keycloak-workload-binding/pom.xml package` | `21ca8ca8b90052fafe3fcfafbdb75afa60541ea0470080f6214bb73c5f56dbda` |
| Complete Server with prepared fixture | Exit 0, 1,462 cases including 11 real-issuer controls, zero unsuccessful counters, no remaining owned fixture paths or containers | `87eff9a7c414a7efdaad3c50f75cba98e1edaea4a80c9361c29ce67d37c26c85` |
| Complete AppHost with topology opt-in | Exit 124 after 12 minutes, no complete-project summary | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| Package archive and dependency inventory | Original source, exit 0, five cases | `0f7e4b97443e54aca647179972594d13bb587afcbf151fab8228148587ea844a` |
| Nightly provider classification and redaction | Original source, exit 0, sanitized report produced | `a74203cd29616155403e481cbfae3f7946dabeb566cec9695403275027daadc5` |

The selected delivery release `v6.3.1` still pins `Aspire.Hosting.Redis` and shared Aspire setup at 13.6.5 and has no central `Aspire.Hosting.AppHost` entry. Folders' standalone audited build uses its existing Builds dependency. Delivery would change that dependency and needs a qualified immutable release carrying the compatible catalog and runtime authority.

All three product composites already exist. The complete Server wrapper enters the real Platform Keycloak launcher, which requires `target/keycloak-workload-binding-1.0.0-SNAPSHOT.jar` before running any cases. The legacy `scripts/prepare-ci-topology-projects.sh` builds this fixture. The reviewed shared `v6.3.1` build runs the solution and its recognized managed .NET build declarations. It has no corresponding Maven fixture build. The preparation path must supply this artifact once before the hook. The qualified disposable component used Keycloak 26.6.4 (`sha256:0aae0de7fca85525f727d3354df17896092de8bb26ae4c12d89c77e5df8cbce4`) and provider SHA-256 `97d44a5f705d85b05e23ace94fd35d31ce8c4dad3fc6ea7fc5b9f6d9616f9302` with actual TLS validation, independent RSA verification and package-bound runtime identities. [The earlier qualification design](implementation.md) records the distinct cohort and provider requirements.

The AppHost command enabled `HEXALITH_FOLDERS_RUN_ASPIRE_INTEGRATION=true`. Aspire DCP and durability containers started, but the strict runner buffered test output and produced no summary before the deadline. The timeout left one test process and two uniquely identified durability fixture containers, which were terminated and verified absent along with their temporary files, containers, volumes and Aspire network. The pre-existing local services stayed running. Separately, FR58's live path still returns `false` at the product prerequisite gate in source blob `df713a1e9b2c619e3940ccf3397ff42afe2df96f`. The complete AppHost hook enables this path, so it must propagate the failure pending the required product behavior.

The two core skips were `ProductionProviderEmitsMetadataOnlyEvidence`, which needs genuine operator provider setup, and `AlpineTlsProfileReceivesExactPackAndRejectsPostAdvertisementStaleOld`, which needs the isolated smart-HTTP fixture. The nightly smoke selects the same latter method in the musl build for two provider versions. The retained scenario needs one explicit lane ownership before migration acceptance.

The [earlier Alpine Docker result](attempt-3/product-verification.json) covers its recorded inputs. This pass checked the pinned-snapshot classification/redaction command and did not repeat the two-version real Forgejo smoke or all shared-stage projects on the new tree.

## Released policy and source discovery

The exact repaired cached-main tree is `b7cdb602409d2c16ed84f11712819503b20b9272`. A disposable qualification commit `5c8cb177b615c3c3957b54d9270db20ac6d0f5b3` has `a53fcb940fa1114fe3ead0af2775af388e39432c` as its sole parent. The changed-path check found only the AppHost project; it preserved all owned bytes, modes and gitlinks against that local base. This scratch commit does not represent a remote push range.

- The latest-pin audited restore failed separately with `NU1506` and no `NU1009` (output SHA-256 `13b29a4d5a531e014b043a14bfddc2071847232443553eacf58decbea8fd83fb`). Tenants `929bac5a9881213b05ddeefc0e2ebd5b0327d819` adds an `Aspire.Hosting.Dotnet` `PackageVersion` at `Directory.Packages.props:36`. Builds `08dc4d275c7fc55c30b6b77bbdae0f36d3884090` already provides it at `Props/Directory.Packages.props:340`. Both set 17.0.0, and their combination is rejected in Tenants, Tenants.Server and Tenants.Contracts. The cached-main dependency graph needs the duplicate declaration corrected before a new build or suite pass can be established.
- Released Builds `v6.3.1` audit lint passed. All eight historical configurations archived by `e5760ca105652f4d89c4f240e0ca455723c9a473` decompressed to their original Git bytes and matched the recorded archive and content digests. No new central audit waiver was indicated by the audited build.
- Released action lint and complete message lint over the exact one-commit scratch range passed. The released guard lock is Git blob `0b4750b5d227a7b68e89cdf4e5e04952a92f0f08`, SHA-256 `e1cee6ebc2ce6f5bb679d3739a7d957052c4fc1d19aebcbb834794f78d232835`. Locked npm installation and signature verification passed in the disposable workspace.
- Current CiCd discovery selected 12 files and failed with 320 diagnostics on the repaired tree. The digest of the sorted-key compact JSON result containing `files` and `errors` is `f43fa669cd6edddc72d04ea349e9e86f93d332b2da8347a1d0ba16e217d5264b`. The CiCd scanner and PowerShell parser blobs are `f908dc071f02593a7e9628e1ef9411d483eb786d` and `19d041f63e62182a1b569d04dcb566288f70f816`. Failures still include unresolved PowerShell command operands and method invocations. The report is a discovery failure before global cross-module duplicate qualification.
- Production render reproducibility passed at the recorded CiCd inputs. `run-with-temp uv run --locked --script tools/render.py --check` exited 0 with empty output (SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`).

## Adoption checkpoints

The story list marks the pilot, McpCli and Conversations as predecessor checkpoints. Their implementation records remain `in-progress`. Agents also remains open. The latest recorded pilot authentication verdict remains `failed-or-incomplete`. The production registry has no Folders entry. Step 03 leaves the live predecessor readbacks and writes pending, including App access and settings, the preparation push with full exact-input proof, the adopted normal checker, the sole-parent delivery and immediate credential retirement. Folders' own valid post-adoption nightly result is still required. [Pilot authentication evidence](../11/scheduled-20261118-authentication.json) · [Preparation publication procedure](../../../../../docs/pre-adoption-publication.md)
