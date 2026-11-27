# Story 21 local continuation

## Decision

Keep Parties migration in progress. The selected Builds release contains the
frozen publisher timestamp, including the follow-up for the OCI artifact label.
Story 31-1 remains a prerequisite for package-mode native hooks, registration,
and adoption. The pinned EventStore owner graph also still needs package
routing or a supported prebuilt composition that preserves the approved
source/package boundary. Live AD-21 settings, adopted CI, and CAP-13/CAP-16
nightly acceptance remain unverified in this local build phase.

## Inputs

| Checkout or pin | Commit | Tree |
| --- | --- | --- |
| CiCd | `b6842869c8d034e39313a63528ad77cfc96839c2` | `09bb54d2e329ba1531a2ca1c41adcc606dfcf33d` |
| Builds `v6.9.1`, selected by `builds-version` blob `c76a5987ef9c9702eefa014a153509015dba735b` | `91cb7cba990ffdf82930f9bf8cb68aef41baba76` | `83bf776a4ae75d3302b77fb57efdf53cfe490432` |
| Parties at the CiCd gitlink | `ca637a01829c57d9163fb686a56bc82b094a10d9` | `b2190751363f2276066b4537fc905e51c45a6d50` |
| EventStore at the Parties gitlink | `7435254cc1a148031224eebe1aafd53a8659b2cd` | `f4210d10d8d560a32b7838a2def87e4417f4c0c8` |

## Findings

- Builds release build blob `2aaf0f0abdce031a22ace306da4d52dd9a558f21`
  passes `ContainerProvenanceCreated` as a global property. The selected tag
  contains the artifact label correction `99baf1dbf2dc2c098ea758f16e4e9bacc892ad7a`.
  The [Story 20 readback](../20/ad21-preflight-and-handoff-2026-11-27.md)
  records the immutable published tag and matching commit.
- Builds `NativeTestExecutor.cs` blob `b5d544c47789bb642156ec71fc0b36f10895a828`
  calls `dotnet test --project` for Microsoft.Testing.Platform with build
  and restore enabled, using a private `test-builds` artifacts path for each
  selected run. `PlatformManifestCommand.cs` blob
  `764a2e9ab625b6ec3b484cf334e13f81b32fc01b` compiles the model with
  `dotnet build` in its run workspace. The selected tag therefore cannot
  meet the build reuse contract in [story 31-1](../../../../implementation-artifacts/prerequisite-21-native-build-reuse.md).
- Package-mode owner graph evaluation succeeded on SDK `11.0.100`. MSBuild
  evaluated the three project files below from a disposable Git archive,
  with the selected Builds `Props/` in a sibling tree. It used
  `Configuration=Release`, `UseHexalithProjectReferences=false`,
  `UseNuGetDeps=true`, `HexalithUsePublishedSdkForHostedTests=true`, and
  `HexalithEventStoreVersion=5.3.1`. Only `IsPackable`, `ProjectReference`,
  and `PackageReference` were queried. Each SHA-256 hashes compact,
  sorted-key JSON containing the project name, packability, and ordered
  source and package reference identities.

| EventStore project | Project blob | Evaluation SHA-256 | Remaining source edges |
| --- | --- | --- | --- |
| AppHost | `68855cf89effbcd82af7ff615b878514711282cc` | `8bde26c5782221ae6bd5307cbf42390f76284794dd4db62dbea3c7383bc723ef` | References the packable Aspire project |
| Aspire | `a5aefb2648a2533b24f647a92c494119a9c42125` | `60596c45a3ffdee021146c23955c54cf9363d7fb44c839bbbc50c22ff2bd07aa` | References Contracts, Client, and ServiceDefaults |
| Host executable | `46928a56031ffc623cc0d642daf596103da649bb` | `29558a27f726dd63430019bb0c146fbadbd6c695c62ab9bacf97b8d30fbfcf46` | References Gateway |

- Parties commit `1acee4cc506d70fcf4169364072f2b93ddfdf75f` added EventStore
  5.3.0 and 5.3.1 to all four compatibility conditions. The changes remain
  in `Directory.Build.targets` blob `77e38e4af12e95bcbf6c3398ca584bf64e9c2c9e`.
  This source check establishes that the compatibility change already exists.
- The published preparation commit is an ancestor of the current Parties
  pin. Later commits restored the tool-only root npm manifests and
  `tests/ci-lifecycle`. The current legacy release invokes semantic-release,
  and the regular CI, lifecycle qualification, and startup-diagnostics
  workflows still invoke the controller tests. Retire those dependencies
  with the delivery cutover while retaining the actual product scenarios and
  the separate browser tooling.
- The locked renderer check ran offline and exited 0 with empty output.
  Output SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.

## Parties product preparation

The local candidate tree is `e166da1f934b39c60de9befdc4469cbe8111e7bc`
on Parties commit `ca637a01829c57d9163fb686a56bc82b094a10d9`. The full-index
diff from that commit, generated against a private index, has SHA-256
`fc6d01ad5c09b223d087bad96c3d95e60502729cc4838ca61360fd218c434411`.
The comparison verified the existing owned file bytes, modes, and gitlinks.

| Candidate file | Blob |
| --- | --- |
| `.github/actions/after-unit-tests/action.yml` | `c58972195d40fcd94751e190f47bf91f1f0d58f4` |
| `Hexalith.Parties.Standalone.slnx` | `3429caebef80f9096385150afb484097d78a6650` |
| `tests/Hexalith.Parties.Ci.Tests/StandaloneSolutionTests.cs` | `93c01655ca6105a0c0b9d3b69cafff6440b47eeb` |
| `tests/Hexalith.Parties.UI.Tests/verify-restored-assets.py` | `f0250c21263fa504146a76c7d16473d25e68cd31` |
| `docs/ci.md` | `1ffd06424ba946fb028cd3edb1cfed0e57e63bae` |
| `.gitattributes` | `7a3b85129b62f6513cef41815fd28b162285cbe2` |

The standalone solution now builds both lifecycle assemblies with the rest of
the Release graph. The browser hook uses the prebuilt UI and retains the
restored-asset probe, configuration and type checks, Chromium scenarios, and
report upload. The probe's temporary fixtures use the product's .NET 11 target.
Hook activation requires the CiCd registration and shared setup for
`tests/e2e` with `browsers: true` and the locked Node/npm versions.

| Local qualification | Result | Output SHA-256 |
| --- | --- | --- |
| Standalone Release build with explicit EventStore 5.3.1 | Passed, zero warnings and errors. The service and all three native suites resolved EventStore package version 5.3.1. | `678e320629ebf4e074d6617ea570a547434ac1851d3e19e968fba1bba33ef7f3` |
| Targeted solution-graph and browser product checks on the 5.3.1 build | 12 passed, zero skipped | `664304dd2a34e0ead27470fcaa1fbade53c9591a6ede8e5bf107518e0055fd15` |
| General `Hexalith.Parties.Tests` on the exact candidate with EventStore 5.3.1 | 2,948 passed, zero failed or skipped | `6adf554b109ab56a4fa9551f47b54aa84f594ccb99a4c3adbc5e409e40a322d4` |
| Owner and focused catalog tests on the base with EventStore 5.1.1 | Owner built and 20 catalog cases passed, zero skipped | Build `8d9e9398723a68d19e2945132d677570d94dc644264c9f8e904a5b2ccf5dcd62`, tests `ebeeb637b3981625d3fcb5dfb79c230a548fc930a1eb28c99b81cf7ece041a4b` |
| Owner and focused catalog tests on the base with EventStore 5.3.0 | Owner built and 20 catalog cases passed, zero skipped | Build `4d72e5f940e61915f6faf36e1c9cc67dff2a62b4c9ffb252bc4ae59f2b448731`, tests `32e48ce10577ad67e89cf20901431d78c7770ac2b26fb18b1023d04de95ee2dc` |
| Browser action npm configuration and TypeScript checks | 21 configuration checks passed and typecheck passed | `046f7a2dce112d10b5074c6fb17448fc731fd55492d1f6b855c48e90373f59cc` |
| .NET 11 restored-asset probe | All five package cache-location scenarios passed | `d4ba4a36488286e066d079b02d121d1eea6486ee117073d76eb668b2357c6471` |
| Playwright Chromium with the prebuilt 5.3.1 UI, Node 26.13.1 and npm 11.20.0 | 81 passed, including semantic and pixel visual scenarios, zero skipped | `19e0e1eb5975b05d736f89028f80d8696b008e849d23700bae7fd7f1c2a33e22` |
| Released Builds audit and action policy on the exact candidate | Passed using the guard's locked YAML parser | `d11a535d580ad6ce56b806cca9103cb4a72892c74a05c358eaf8b63d04960363` |
| Actionlint 1.7.12 on a temporary caller of the browser hook | Passed | `6e34c5b41e47a0d37fa78356d5d192f74b7a72916629a2d55821c00d72d207aa` |

The UI restore assets confirm EventStore Client, Contracts and SignalR at
5.3.1 for the explicit cohort (SHA-256
`2d0eded203dfb0335e7692aa1ba2d573b56edce04d10022716a3283afaed8018`).
The default browser build resolved those three packages at 5.4.0 (assets
SHA-256 `680f35bfad49858d33af045b8ea2e4a68bf37934822062eabc8cfe5c0b2c43db`).
The hook command run used tree `ad949f54884670d4a8efc7aa707db4464dca33a6`,
which differs from the final candidate only in the CI documentation.
The first general-suite run relocated compiled output and failed 25 cases
because the generated MVC manifest referenced the original scratch content root
(SHA-256 `68822a708caa9cda0c0079c288233d7d2fd61224a992220590c82f0d71101f3a`).
The passing rerun built and tested in the same disposable checkout. The
targeted build had zero warnings and errors (SHA-256
`4bbd14c7d61e4e256fe9007e7d20cb01f9c0b1bff093df5b9f321ef2cd940c58`).

The released policy inputs were `Github/lib/audit_lint.py` (SHA-256
`e19abe384db51e6d49b9eace83f771fa5760162d95382d0e1a1baaa0d8220970`),
`Github/lib/guard_actions.py` (SHA-256
`d17711dac3f7a2043098270d677b8560c13636c20ae7112fc396d72662587eea`),
and `Github/guard/package-lock.json` (SHA-256
`5741670cc02027a35ffa002c24e7b99162addade92016cda0995d5b813e49ca0`).

All three container projects accepted the source, version `4.1.0`, and
common created instant `2026-11-27T13:42:01Z` supplied by the selected
Builds release flags and rejected a February 29 in a non-leap year.
MSBuild validated the labels on the Parties base commit. OCI archive and
publication qualification remains pending.

| Container | Label evaluation SHA-256 | Invalid-date refusal SHA-256 |
| --- | --- | --- |
| `parties` | `806104380f0da50393d848dfc19afc9c8b73954703c735ddf6af9d86e1bb2e15` | `5201e973d4f97cab3f4943f7d932b758fff9f1140932699a7b300f2530f6c55f` |
| `parties-mcp` | `1354f2ec6298490a1cf2fd0478d58f89b933e9f0620564e05ba38347780b5d0b` | `80e2e219840c2fbf3040bada0ebfc18ebfcc60ade4623713737d2c5f53210504` |
| `parties-ui` | `58a6360824fa25c57041070f827e8b4637001ac46aa2d46dd1e07b54fedd1a46` | `f840a2cbb7b69ec2b6deb5737ad4069f5b9f1b839a140b6b6036e7803bc631a3` |

## Fresh-main preparation publication

Parties preparation was published to `main` as
`8daf30af7e413278f03f1ea744477e976a78fe16`. The remote branch readback matched
the qualified tree `ce7e4038e3f5a51a4eab3a146f1d1f75b99ec526` on parent
`d5c628f7ce2b88ee5440c6089efad22763319dc3`. The six pending product files
applied cleanly to the fresh parent. The candidate passed the owned file,
mode, and gitlink comparison. The published source resolves EventStore 5.6.0
and Tenants 8.1.1 packages through its default catalog.

| Exact-candidate check | Result | Output SHA-256 |
| --- | --- | --- |
| Standalone Release package build with analyzers and NuGet audit | Passed with zero warnings or errors | `305860ad6a05cac52c72e9b6da7463e339d58780eb4584f681c6328d7f96129d` |
| Catalog tests | 20 passed | `eb0f05a52f98dd7f392876943444feb1f92c66e2df572fae30a868ad5d1a8a51` |
| CI product tests | 436 passed | `0cc89ae56a8e8a989c951a86f7dccd7d7a6cfece0a2992f86091c5138df59258` |
| General tests | 2,965 passed | `b84ba63c4aa5010463c846516ff044143e14e10ae35d66ec635cbf536f31c89c` |
| .NET UI tests | 487 passed | `72f2f91eafbcb54004b3906de974d42deb72a2d78270b447db0abaa8eed58fdb` |
| Additional standalone test assemblies | 2,588 passed. One existing projection test for the legacy SDK path reported a skip with the current generation-capable SDK. | Projection log `f052df31fd2e80196fc9a8f1252e991fba6cd10424e98c641ed3319eda0cc880` |
| Browser hook | 84 Chromium tests and five restored-asset scenarios passed | `d6e43641b39c0e6b228feaf3e2d637f504f5881973fa263aebde3986708e2b62` |
| Runtime preparation with build reuse | 13 artifacts prepared from the completed build | `6d3eb613ab591f40e2a9d52a174a1fa7904bf3275efc647f7eb387ac4033d9a2` |

Released Builds v6.9.1 audit and custom-action lint passed on the exact
tree, including the locked npm install and signature verification. The
published commit message passed the released and module commitlint policies
(message SHA-256 `3634354069b9d5962d67d413b62d6081d8767ff4b5a5e959f161b547d2db9e88`).
Native execution, registration, App adoption, hosted acceptance, and
nightly qualification remain pending.
