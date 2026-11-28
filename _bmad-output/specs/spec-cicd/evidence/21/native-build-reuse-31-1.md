# Story 31-1 local native build reuse qualification

The local change adds the opt-in native build receipt to Builds, along with a
Platform companion for the bounded Parties package composition. The Builds and
Platform worktrees hold local implementation changes. Publication and pin
selection require the central Builds release process.

## Source identities

| Input | Commit | Tree |
| --- | --- | --- |
| Builds implementation baseline | `a0c8b64ec1a9492220a4caa5487574296263f8e1` | `7f11bdbfd7184ef6651e1dc419099ca9f97ab3b0` |
| Platform companion implementation baseline | `e51cf194ac1caac65feb233c8c42491a7895518f` | `6865ea361b1463c8e62e3989ce023bbd83051744` |
| Parties qualification source | `8daf30af7e413278f03f1ea744477e976a78fe16` | `ce7e4038e3f5a51a4eab3a146f1d1f75b99ec526` |
| Parties-pinned Builds catalog and EventStore gateway seed | `91cb7cba990ffdf82930f9bf8cb68aef41baba76` | `83bf776a4ae75d3302b77fb57efdf53cfe490432` |

Parties records Platform `a670a4c51d76f63f3142e38f02542a246e1926fb`,
EventStore `5484fae6c284cd8fe70b51bf921c5b31509b6c27`, and Tenants
`d58f24d8d6909d7498ecec34955e7f17720c1ba0` as direct gitlinks.

The initial qualification inventories include untracked implementation files. Each
inventory digest hashes sorted UTF-8 relative paths, a NUL separator, the
file SHA-256 rendered in lowercase, and a newline.

- Builds 33 changed files, SHA-256 `e72396fe687523898106d23dbaf3f8663af49b4b0f998defd09dd4320d0a7457`.
- Platform 9 changed files, SHA-256 `22e6204cacf66705e189852cef0e9341c72b327bb155f53e6e7b5cc526df761d`.

The acceptance audit wired the producer into the validated `nativeBuildReuse`
configuration flag. The hosted build exports its receipt after the audited
Release build. The ordinary local checker applies the same audit flags and
has no hook receipt to publish. Schema fixtures verified the omitted and false
defaults, the true option with a manifest, and rejection of invalid options.
The shared receipt validates each profile's composition inventory. Its model
defines and checks the runtime-specific roles.

## EventStore package owner

The package-only Builds gateway seed compiled in Release with the .NET
11.0.100 SDK and the all-dependency NuGet audit at level low. The restore
graph contained zero project libraries. The four required EventStore
5.6.0 DLLs matched their archive members byte for byte, and each archive's
raw SHA-512 matched the Platform package lock.

| File | SHA-256 |
| --- | --- |
| Gateway build log | `bdb9910770de55649047f4dd4f8c9aa16e31a49769d6815e9ea6e71be6011e67` |
| Restore assets | `6746987ca608929e905d4bb3467378d257af6f80f0310c1ce80af29aecdd08ee` |
| Gateway seed dependencies | `131dfdbf086ab5a4937c1cf0d91eff1a6b5ef37b42697a57b94567f4771809b9` |
| Builds gateway seed DLL | `8f43fe657234b6f9eeb3bb03d53fec3f4e4411688e23559bcca0b9efcc9e9e21` |
| EventStore Gateway DLL | `b8e9c38e1c0b68ff7aeb2d5f86cadfe6bab1f68371f3218591bfc4c68228527c` |
| EventStore Server DLL | `cb0cc2f6d4787c310bfb78e32c0f4fef5bb2bef384d95eb2760274c681d15e59` |
| EventStore ServiceDefaults DLL | `b457878402d740852523d7b12848673094a0f2e30f79d2e9442419e3cbdcd99d` |
| EventStore Contracts DLL | `775f53f93312e9bdcf29caa5db4fa595cd1dfe93c6b53ea36d08646ace27ef2d` |

The restore and runtime dependency graphs agreed on their NuGet content
hashes. The signed archive's raw hash is a separate identity. The producer
checks the NuGet-normalized hash through `PackageArchiveReader` and records
the raw archive SHA-512 separately. A package-reader probe recovered the
expected normalized hashes for all four signed EventStore archives. The owning
Tooling restore resolved the central `System.Security.Cryptography.Pkcs` pin at
11.0.0 and passed audit with zero warnings or errors.

## Parties package outputs

The exact Parties standalone solution compiled in package-mode Release with the
.NET 11.0.100 SDK and a transitive, all-level NuGet audit. The checkout used its
recorded direct Builds, EventStore and Tenants revisions. The build reported
zero errors and one optional RuntimeArtifacts warning for the absent direct
Memories source checkout. The build log SHA-256 was
`a6d597c4d72acdda59c3cd09ca09c3ac71d70527991ad15c7cd44122c1949b08`.
The declaration SHA-256 was
`a02a5e6c2213841ef1f0a573f3b69c5077c39bc9fcdb754b262c74f4bfb9d625`.

All three native test graphs resolved EventStore packages at 5.6.0 in both
restore and runtime metadata. Tenants is a Platform dependency and is absent
from these three native test project dependency graphs.

| Profile | Restore assets SHA-256 | Runtime dependencies SHA-256 | Entry DLL SHA-256 |
| --- | --- | --- | --- |
| `platform-package` | `4f694e0073aab27e8f03b3494d927b9429caaf38e6db3bd91e07d187f032593d` | `45d751129f25cf561d1bacd7f2c3c96516ebe73ba6bae9418fb2ab40da3aba43` | `0daa8b6a84f53e4925db8b28c8aebe090563a4f44d2d81139ae77bb749885a0e` |
| `lifecycle-package` | `51fa7ce3d787f9d4c7cf21077cc6d7725b78e96f6ab2ff27f0ee4b73280a3d12` | `a8646e6cdc125b43961f4b361eae0c8ecfb0d85878f8175595761681cd4d2f5c` | `804e2ca69d2a568570484e6528d1cbe50aa5ae620b496b550612d95ca05fa66c` |
| `attached-lifecycle-package` | `87f9ecda41e7b0f4fe5c5b0e076035c0fef84aaf9973527318489cbdb5590a3a` | `fa341c2def0c1b1bd864b1cb0233c41355aa8865e523752e1666282274850184` | `d3519c382eb3ba9926da74add529dc81ea79619926a7e231dbd4ebfb0423354d` |

The local Platform companion also compiled in Release against the selecting
Builds catalog and the candidate Tooling assembly. Both its restore and runtime
graphs resolved EventStore 5.6.0 and Tenants 8.1.1. Its restore assets SHA-256 was
`2ec0fea11bd0b96599235b0a10285f0474139fe8c89dba7edf460b2098a2283b`, and its
runtime dependency graph SHA-256 was
`3c4d28fa9026900695e7fb61d6e7183512a3cceb71b3df1bc49fb2bcb627f5fa`. The
Tooling assembly SHA-256 was
`d5aa28997a7cbeb965ea501ed70451d006cf42904c261be45eec52d30d72c223`.

## Regression results

| Check | Result | Output SHA-256 |
| --- | --- | --- |
| Builds CLI, native executor and attachment tests | 256 passed, zero skipped | `ddb320f9389a968469855b99c1312a6b87b9775106c3970be096a49a5ced434e` |
| Platform companion Release build | Zero errors and six existing Aspire obsolescence warnings | `01aac8ae917c0178792782b9be1d6efe88fff53b8fdea2732f2ee8f62ad0bcd5` |
| Final audited Builds Release compile | Zero warnings and errors | `c6d769e164803c9ac473f0794e8051156cd1d7cbb089bda88276df9a305900b2` |
| Prepared CLI and executor fixtures | 10 passed, zero skipped | `6aba4eaa37e8f780a7c94577f35fb4b9a6336f75cd4732f8ad38d3b6e8658007` |
| Focused fixtures after the shared composition-role audit | 10 passed, zero skipped | `3a2735109da1673992d56c7ee189de7019d46544871fbbfef140ebe8785ff965` |
| Prepared fixture child-process trace | Recorded the direct private assembly launch and no compiler or restore process | `abfb6def33d2c8cc5232a4feff7f365ea0ef1db8558bc66a313b4ddb6e737239` |
| Final Platform composition test project Release compile | Zero errors and ten existing Aspire obsolescence warnings | `3e080646fa29dc1f1e57a2d425aecda4b85a86a74a6b131cdd912544d4b95493` |
| Platform prepared entry and current-owner proof tests | 10 passed, zero skipped | `f876887d3314b7479fd0ec78c68df3beb1c9b8eb4a1e58289ed0ddd70a6a5f11` |
| Shared CI Python pipeline | 55 passed, including opt-in audit, sealing and checker compatibility | `a2d3f974de79ff1a4a4f1d6d6171d77fcf1c33ae8ee2c20005efa3929d19e361` |

Private-index diff whitespace checks passed for both worktrees. Builds diff
SHA-256 `6c6371af81e48028c197125671cadd5f1828f21d16978d5518b21ec0f321be77`.
Platform diff SHA-256
`190e3dcb3f8d63c792b726082d80c5cac76944220be8d6042b81ed5699bcf226`.
The CiCd locked offline renderer check exited 0 with empty output.

## Source profile comparison

Every direct Parties gitlink was checked out at its recorded revision in a
disposable clone. The gitlink inventory SHA-256 was
`898d18c5f2b9f8149b50f29a193a60226aad3b0b76dea9f42fcbd79407db6bfc`.

- A local Release CLI run failed preflight with `HXR012` because the ambient
  Dapr home used runtime 1.19.1. Result SHA-256
  `4a0c9a2017bba897ee725835f7486a2c3423f3ef3355a5d73b4956531daf0cbc`.
- With Dapr CLI 1.19.1 and runtime 1.19.2, the local CLI and AppHost Release
  outputs reached Platform startup. Run `82d4eccb7c1d5451a417975b344ead43`
  failed readiness with `HXR025` before native execution. The runner issued
  a successful scoped `down`, and the run's label found zero Docker
  containers, networks or volumes. Result SHA-256
  `dd7bbcd92df6495ded2f42a995544757ed67244e122789b3a652af973ea97c2c`;
  cleanup SHA-256 `7cc15a698f741191495a82d36ab22deb05e3657ce3c6ccf63db25be2af92282e`.
- Published CLI 6.9.1 with the same runtime and source pins passed readiness
  and native TRX for run `6fb6baf5d07252a5eb7d5061c1e18537`. The run's label
  found zero Docker containers, networks or volumes. Cached package SHA-256
  `e3536965d0aab4ecac6251376de37fd8e9144539b491f00a2a032747b856c80c`.
  Result SHA-256 `c4b5cf075ebd5c11184e7556ba2cdec8012a3e41d62657f7e1aee503109becc2`.
- A local package built from the final working tree reached owner preparation
  for run `ff7af4303fa1493f8c631e1820455ecf`. The CLI reported `HXR027`
  with `InvalidOperationException` in owner preparation and unhealthy Memories
  access-telemetry resources. Native execution did not begin. Scoped `down`
  succeeded, and the run's label found zero Docker containers, networks or
  volumes. Package SHA-256
  `a7a5712fe66445082e6f1b5a29710f9cff1bc24117d076c0644945dcc7655a96`;
  result SHA-256 `ce4e7b1971481b651009f89ad23ec846622871a2342480bc68bfc547ae2f414b`;
  cleanup SHA-256 `af62dcfa0fcee91fd9725518edc75eaf13c8cff510ff4a913cf825dc6dbba687`.
- The same local packaging procedure applied to clean Builds main
  `a0c8b64ec1a9492220a4caa5487574296263f8e1` passed readiness and native TRX
  for run `a660a1b34f6cd8e9621106eea7680526`. Its run label found zero
  Docker containers, networks or volumes. Package SHA-256
  `dffc89540ab9b9f4cf12e7f4f5e94a53e71bf927710635d112ee7039043d292d`;
  result SHA-256 `187da7c71667c0322331999e06d3705087835418b637f956c0d4313ed2c8745b`.
- A controlled repeat from the final working tree passed owner preparation,
  readiness and native TRX for run `34f2e1e53bd733efe31489e6980952a7`.
  Its run label found zero Docker containers, networks or volumes. The
  earlier source startup failures did not reproduce on this run. Package
  SHA-256 `e0d88e4e9dfb18ae9232c7f2e2d625789973233b248fd8dead2c4c1ba0a37152`;
  preparation summary SHA-256
  `f6eda919c83f3bb3f585cdc4b617808d2ccb562620a0583b940296fbd42c9cf7`;
  result SHA-256 `b4685039b2df165ea92d282cf6b2c3b1d0741b0dc124f84a61b11be6d34d4d4c`.

## Exact live qualification boundary

The recorded Parties Platform checkout lacks the prepared entry point.
The candidate producer checks `PlatformAppModel.ComposePreparedRun` in the
model's Release assembly metadata, and the runner requires that same entry
point under an authenticated run plan. Platform's package proof checks the
working checkout against the selected Platform revision and its recorded
Builds catalog. Using the local companion under the old gitlink would
change the selected authority.

The live package profiles, live cancellation and attachment expiry remain
pending. A compatible Platform source and released Builds CLI are needed for
the exact-pin live package qualification and CiCd selection.

## Branch publication

The Builds feature branch was pushed and read back at
`e7140340850d98ac2710adce033629014f7d2804` (tree
`40919aa3c68ee776d2d57fcd3f7ca71bfd5b95a8`). The feature commit
`dd5110b92c89a6723dcbd13ff44de19c9e1e4f05` (tree
`a502ac71982f48f71210f4e269c4f13296379ad9`) starts from freshly fetched
main `bb38c3e42f48f37de76c77983e4de83d99f619b7`. The authoritative
catalog now carries the NuGet.Packaging reference. The required full audit
refresh covers 336 packages and binds the audit to that feature commit.

| Check | Result | Output SHA-256 |
| --- | --- | --- |
| Feature commitlint | Passed | `6066fe5dfab91cf3b8b76295987faa4727d17c1d5ecc675b0075cdff9b632a75` |
| Audit commitlint | Passed | `620a4f40aeb47e5689f58ba93260be0cb3e1bc87f6f077eb91014921600bec0c` |
| Selected Builds Release tests on the feature commit | 156 passed on serial rerun. The earlier parallel run observed one process-discovery failure. | `897aa0d11deaff7d0db8d32609bdb246293fa3a34dd124f1a91fd5750ac5baca` |
| Pipeline and configuration tests on the refreshed base | 55 and 24 passed | `9726e78201fac18f1b2b9c1baa3b47004799d7b83927aa68d1f59ac73419551b`, `72c0072a554190fc2372a4462ce211c30bdb086a3b9db88b59a84fca38085023` |
| Committed central catalog and audit validation | Passed for 336 packages | `6abbe2c7c62de1550608434f6c78f6c292254167e6cbfeb3fa0d4f713a0cb2e2`, `d67e495e00d58ca62cd6422b8b593b42b57392aad7d0078048a654a1760fe813` |

The Platform Release build with its committed Builds pin
`91cb7cba990ffdf82930f9bf8cb68aef41baba76` failed with `CS1061` and
`CS0103` for the prepared-build API. Output SHA-256
`ea1e81a1fff8d73988dcbd479c0ac4bf681efb642d6128d3b1ba536a4b5db307`.
The Platform candidate and the parent CiCd record remain local under the
pre-push rules. The Builds branch push does not establish a released tool.
