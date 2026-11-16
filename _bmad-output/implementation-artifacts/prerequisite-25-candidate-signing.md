# Proposed candidate-package signing for product checks

Status: proposed; trust decision pending. This does not authorize a signer,
change NuGet policy, enable a hook or establish preparation-push acceptance.

## Problem

The shared package-consumer runner packs the exact existing Release outputs.
Those fresh local packages are unsigned. `references/Hexalith.Builds/NuGet.ci.Config`
requires signatures and trusts only nuget.org's repository certificates. NuGet
adds its repository signature only to published packages. Consequently a local
consumer restore cannot pass this policy today. Unsigned-package acceptance,
signature-error suppression and substituting previously published package bytes
would fail the existing contract.

## Proposed minimal solution

Use one signing identity for each isolated validation job. Sign only the exact
module packages that the validated manifest selected, before freezing the feed
and executing the six consumer restores. Create the key and certificate under
the private job directory; remove them when that directory is cleaned. The
identity grants no release, publishing or external repository permissions.

The proposed temporary identity is a short-lived, self-signed code-signing
certificate. This explicitly requires author trust for its exact fingerprint
inside the private consumer configuration, including `allowUntrustedRoot=true`
for that one certificate. Signing uses the SDK's corresponding
`--allow-untrusted-root` option; signature checking is still required during
restore. This is a proposed local-candidate trust exception, not a change that
has already been authorized or installed.

The consumer's private NuGet configuration keeps `signatureValidationMode=require`,
the shared public repository certificates, vulnerability audits and exact
candidate-ID source mappings. Add only the explicit candidate signer trust
needed for this job. Never modify machine-wide trust or shared production
NuGet configuration. Existing public repository signers retain their trusted-root
requirement. Approval of this temporary-signer option must cover the narrowly
scoped self-signed author trust described above; without it, retain the refusal.

Keep product-specific archive assertions in the module. Narrowly recognize
NuGet's signature metadata after authenticating it; retain all existing payload,
dependency, symbol, informational-version and original-output checks. Freeze
and compare the signed archive bytes consumed from the isolated feed. Private
keys and passwords must not enter reports, artifacts or command-line logs.

Alternative: use an existing organization code-signing certificate with an
already trusted chain, supplied through its approved credential path. This
avoids introducing a temporary trust identity but adds a protected signing
credential and its lifecycle to CI. No such credential has been established.

## Concrete changes after a decision

- Builds `Github/lib/product_validation.py` and its existing tests: sign the
  exact candidates and construct the narrowly scoped consumer trust inputs.
- Timesheets `scripts/release_common.py` and retained package tests: recognize
  authenticated `.signature.p7s` while preserving exact product payload checks.
- Builds `Github/product-validation/README.md`: document trust lifetime,
  source/manifest binding, cleanup and separation from publication.

Qualification must reject unsigned, altered, expired or wrong-signer candidates,
wrong feed bytes and changed original outputs; it must preserve shared public
package verification and audits and complete all six actual consumer runs.
Use an isolated real-SDK probe before enabling the production path. This is
one addition to the existing runner, not a separate package service or PKI system.
