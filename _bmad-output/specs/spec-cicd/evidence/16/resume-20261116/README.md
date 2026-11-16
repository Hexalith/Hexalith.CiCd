# Story 16 resumed prerequisites

Builds main contains audit fix
`fa6dc2864ac65c6244b111fa9ecc5e7a78722e3e`. Its
[exact-source CI](https://github.com/Hexalith/Hexalith.Builds/actions/runs/43951398012)
must complete before selecting the supporting release. The refresh retained all
317 selected versions and 150 unaffected families. Production validation, 113
generator scenarios, 109 validator scenarios and owning root commitlint passed.
See the [catalog receipt](catalog-preservation.json),
[verification receipt](catalog-verification.json) and
[publication receipt](builds-publication.json).

Supporting source now also contains path guard fix
`27e8fba9736a4825d44c40c638c5e6f9b65ab81e`; its
[linked CI](https://github.com/Hexalith/Hexalith.Builds/actions/runs/43956522607)
exposed a catalog lookup failure: the unmaterialized Tenants default reader
selected the conditional 7.0.7 compatibility value instead of the owning 8.0.1
default. Remediation remains pending. Unsafe scratch spellings fail before tag
fetching or output/tool work. All 152 finalized preparation/Windows/local/release controls passed with
zero skips, and the eleven preparation cases also passed on Python 3.12.13.
Concurrent catalog updates were preserved; the eventual released catalog must
drive a fresh successor-lock qualification.

The [administration receipt](administration-receipt.json) records ordered AD-21
provisioning and readbacks: existing App membership, acknowledged deletion of all
296 inventoried legacy CodeQL analyses, exact main/v* protections, main-only
release environment, scoped NuGet policy 27245, isolated Zot identity and additive
shared grants. The terminal CodeQL response remains exactly HTTP 404
`no analysis found`; it is accompanied by acknowledged deletions and successful
metadata reads. Legacy policy 18928 and other existing access remain. Immutable
releases must be enabled immediately after authenticated adoption.
Existing legacy workflow runs can upload new analyses; refresh the legacy
inventory before the protected push/adoption sequence.

The local module candidate is
`47e8dde1600b7a72b86532e22644dca5d952a4ff`, reapplied onto fresh main
`f1a2b3da468760d4188f604045deb098af8ead52`. Its
[preservation receipt](module-current-main-preservation.json) records unchanged
runtime source, actual warm-path benchmark, live projection suite, frozen fixture
and named owned paths. The central gate inventory classifies the newly encountered
historical measurement-envelope gate. The candidate is unpushed; tool/Platform
prerequisites, successor locks and released-input execution remain pending.

[Private Docker feasibility](private-docker-feasibility.json) passed with an empty
real daemon and exact SDK 11.0.100 container sharing its network namespace. The
SDK reached an inner service on private IPv4 port 6379 while the user's existing
Dapr IDs stayed unchanged. Owned daemon resources were removed. This establishes
an available isolation approach; it does not claim actual Dapr or product execution.


The [fixture-protocol fix receipt](conversations-protocol-fix-verification.json)
records five locked qualifier controls passing on Python 3.12 and 3.14, all four
unchanged protocol controls passing against the actual held product, and clean
owner checks with Conversations uninitialized. All authenticated online checks
passed. The unchanged delivery tool suite exceeded its local 600-second bound;
the full local global lane is not claimed passed and the normal hosted global
gate remains required. No timeout or gate was changed.

Raw authenticated API/UI observations, failed probes and useful logs are retained
locally outside the repository. These receipts contain sanitized state and exact
identities; passwords, tokens and secret values were never persisted locally.

Still required: successful supporting Builds CI/security triage and acceptable
release, genuine tool pin and Platform prerequisites, committed candidate render,
full exact-input product qualification, protected preparation push, live validator,
App adoption/preservation, normal checker, full Linux/Windows CI, immediate legacy
cleanup and the next genuine scheduled-night outcome. No adoption or nightly
acceptance is claimed here.
