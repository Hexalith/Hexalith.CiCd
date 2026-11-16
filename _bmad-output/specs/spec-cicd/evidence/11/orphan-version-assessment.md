# Removed legacy versions and the real next-version decision

No package version, tag or release was created, replaced or forced by this
assessment. Existing NuGet packages remain untouched.

| Removed orphan tag version | Exact live NuGet observation |
| --- | --- |
| Commons `2.30.2` | All twelve legacy package IDs return HTTP 404 from their versioned nuspec endpoints. |
| Poly `1.19.4` | Both package IDs return HTTP 404. |
| Poly `1.19.0` | Both package IDs return HTTP 200, with exact ID/version and source commit `1eefc400cf972288c8b6e44b5de9f1d6b3ffddd0`. |

`orphan-version-nuget-readback.json` retains every URL/status and the published
nuspec identities, including the historical repository URL difference for the
code-generator package. These were bounded unauthenticated GETs, not push or
delete probes.

Ran the unmodified `v6.0.6` shared `compute_version` and its real integrity-locked
plugins in a disposable workspace. The shared `Git.fetch` obtained fresh
anonymous full main/tag objects, avoiding stale local refs; all three deleted
tags were actually absent. On exact current preparation mains, the resolver
selected Commons `v3.0.0` and Poly `v2.0.0` as the highest reachable stable
bases. Both reported `no-version: true` and “nothing to release.” Inputs,
resolver/plugin hashes and exact results are in
`actual-next-version-assessment.{json,log}`.

Those naturally selected bases are newer than every removed orphan, including
the existing Poly `1.19.0` payloads. The current decision publishes nothing; any
later normal increment starts from the newer base rather than reusing a deleted
legacy version. The actual scheduled nightly must still establish its own
then-current decision and outcome. The shared publisher's live ID/version/source
verification remains required for any publication; this read-only computation
does not authorize an existing conflicting payload or substitute for the real
night checkpoint.
