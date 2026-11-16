---
title: Sign isolated candidate packages for product checks
status: done
baseline_commit: 0f25d19ba712eee9aae59d118251b854bbffd120
implementation_baseline_builds: 6db97d4e9da392ef691ed3f367e73f1b7d2ef318
context:
  - /home/administrator/projects/hexalith/cicd/AGENTS.md
  - /home/administrator/projects/hexalith/cicd/_bmad-output/implementation-artifacts/prerequisite-25-product-validation.md
  - /home/administrator/projects/hexalith/cicd/references/Hexalith.Builds/Github/lib/product_validation.py
  - /home/administrator/projects/hexalith/cicd/references/Hexalith.Builds/Github/lib/tests/test_product_validation.py
  - /home/administrator/projects/hexalith/cicd/references/Hexalith.Builds/Github/product-validation/README.md
  - /home/administrator/projects/hexalith/cicd/references/Hexalith.Builds/NuGet.ci.Config
  - /home/administrator/projects/hexalith/cicd/references/Hexalith.Timesheets/scripts/release_common.py
---

# Candidate-package signing for product checks

Approved: the human answered **“do it”** to the temporary job signer proposal on
2026-11-16. This authorizes the scoped self-signed author trust below. It does
not authorize changing production NuGet or machine trust, publishing a release,
enabling adoption hooks, or declaring a migration complete. Platform story 26
remains approved and stopped. Preserve concurrent work in every repository.

<frozen-after-approval>

## Goal and boundary

Make the existing shared runner's six isolated Timesheets consumers accept the
exact fresh candidate packages while keeping required signatures and audits.
Fresh local packages currently fail NU3004 because shared NuGet policy trusts
only nuget.org's repository certificates. Never accept unsigned packages,
suppress NU3xxx/audit failures, substitute published package bytes, rebuild the
module during consumers, or broaden candidate source mappings.

Use one short-lived, self-signed code-signing certificate per private validation
job. Sign only the exact regular packages selected by the validated manifest;
symbol packages retain their payload contracts. Keep keys/certificates in the
private scratch directory and clean them on all exits. No private keys or
passwords in reports, artifacts, environment dumps or command-line logs. Use
existing SDK/system tools; avoid a service, permanent PKI, new application
framework or unnecessary dependencies.

The private consumer configuration retains `signatureValidationMode=require`,
the shared public signers and exact candidate-ID mappings. Add one author trust
entry pinned to this job certificate's SHA-256 fingerprint, with
`allowUntrustedRoot=true` only on that entry. Signing may use the SDK's
`--allow-untrusted-root`. Never modify global/machine trust, public repository
signer root requirements, or shared production configuration. Preserve NuGet
vulnerability audits and exact feed-byte, package-version, informational-version,
assembly/symbol-output, dependency and consumer assertions.

Authenticate each signed candidate against the job identity before admission.
Reject unsigned, altered, wrong-signer and expired candidates. Retain the
module's exact archive/payload/dependency checks. The simplest valid ordering
may validate unsigned payloads first, then sign and authenticate, proving that
all ZIP payload entries are unchanged and only NuGet signature metadata was
added. If that ordering suffices, leave Timesheets validators unchanged. If
module validators must inspect signed archives, permit `.signature.p7s` only
after authenticating it; never simply whitelist an unauthenticated filename.
Freeze the signed feed and its regenerated ledger before consumer execution.
Keep all existing mutation/provenance checks throughout restore/build/run.

## Implementation map

Builds `Github/lib/product_validation.py` owns this addition and its integration
with the existing validation flow. Its existing test module owns behavioral
regressions; a focused real-SDK test/probe must establish actual trust behavior.
`Github/product-validation/README.md` documents trust lifetime, exact selection,
cleanup and separation from publication. Timesheets `scripts/release_common.py`
and package tests change only if their authenticated metadata handling requires
it. Do not edit owned CI/CD portions in module checkouts.

Read each owning repository's guidance/configuration before edits. All ad hoc
build/test/probe workspaces and outputs go beneath `$TMPDIR`, supplied by
`run-with-temp`; useful logs/results live outside scratch. Wait for child work
and cleanup. Builds starts from fetched current main. Do not commit, push or
perform remote operations in the implementation handoff; the coordinator owns
final Git work under the human's earlier push-to-main authorization.

## Tasks & Acceptance

- [x] Prove the minimal trust/sign/verify path with the installed real SDK in an
  isolated job, including negative candidates. Use no machine trust mutation.
- [x] Implement per-job identity/signature authentication and private author
  trust in the existing runner; retain original build outputs and all audits.
- [x] Preserve archive assertions and signed-feed provenance/mutation checks,
  using the smallest correct ordering; update module code only if necessary.
- [x] Extend existing meaningful behavioral tests for fail-fast signing/trust,
  unchanged payload/output, wrong feed bytes and cleanup. Run affected tests.
- [x] Run actual six Timesheets consumers against a fresh Release/package build
  with current catalog, exact version and signed candidates; preserve SDK11 and
  net10 compatibility. No need to repeat unchanged expensive product suites.
- [x] Document and report exact tested revisions/hashes, commands, results and
  any incomplete acceptance. Do not claim publication/adoption acceptance.

Given an approved isolated job, when exact candidates are packed, signed,
authenticated and consumed, then all six actual consumers pass and the public
NuGet policy is preserved. Given unsigned, tampered, expired, wrong-signer or
wrong-feed candidates, when validation runs, then it fails before consumer
execution. Given success or any failure, when the job exits, then temporary
signing material is removed and module Release outputs remain unchanged.

</frozen-after-approval>

## Implementation Notes

- Approval recorded; implementation started from the canonical revisions above.
- Coordinator clarification on 2026-11-16: reusing an existing public RFC3161
  timestamp authority through the SDK is within the approved signing scope.
  “Avoid a service” means do not build or operate a new service or PKI. Preserve
  timestamp verification and fail on refusal; do not create a local TSA or add
  timestamp root trust. The real SDK requires a timestamp to avoid `NU3027`
  under the retained warnings-as-errors policy. References:
  [Microsoft signing guidance](https://learn.microsoft.com/en-us/nuget/create-packages/sign-a-package),
  [DigiCert RFC3161 endpoint](https://knowledge.digicert.com/general-information/rfc3161-compliant-time-stamp-authority-server).
- Implementation and local acceptance completed on 2026-11-16. Builds changed
  only `Github/lib/product_validation.py`, its existing behavioral test module
  and `Github/product-validation/README.md`; Timesheets code is unchanged.
  Unsigned payloads are validated before signing, then every original ZIP entry
  and all symbol archive bytes are preserved. Only exact regular candidate
  archives are signed/authenticated; keys are removed before consumers and the
  signed ledger/feed and original Release outputs stay under mutation checks.
- The SDK can accept an expired timestamped signature (and can report
  untimestamped expiration as warning `NU3037`). Admission therefore separately
  validates the job certificate's current validity and self-signature with
  OpenSSL before fingerprint-pinned SDK verification. This preserves the scoped
  job lifetime even with a valid timestamp.
- DigiCert's HTTPS endpoint refused connection in the real SDK probe. The final
  implementation uses its documented `http://timestamp.digicert.com` RFC3161
  endpoint and preserves SDK timestamp authentication, chain/root requirements
  and failures. No local TSA or timestamp trust exception was introduced.
- Local results: 36 behavioral cases passed; the 20-command real-SDK probe
  passed, including unsigned, altered, wrong-signer and expired-certificate
  negatives. A fresh full Timesheets Release/package solution build passed
  with zero warnings/errors using SDK `11.0.100` and net10. All six actual
  isolated consumers passed at `2.1.1-preview.0.3`; all twelve original
  assembly/symbol hashes were unchanged and signer workspaces were removed.
- Tested Builds base: `6db97d4e9da392ef691ed3f367e73f1b7d2ef318` plus this change;
  Timesheets: `b325a0b47d642f1711f49e589509ca89ac585bca`. Runner SHA-256:
  `7c061a8ec84a550778e0ea10c560415a67f34fb1b968e5b3c3876a6647a38d00`;
  current catalog SHA-256:
  `7c76e92b8986c9470154e1502b3395df019d29f61853de934cf35db73a41a54b`.
  Exact commands, dependency revisions, input/output hashes and result receipts
  are in `../specs/spec-cicd/evidence/25/candidate-signing-summary.json` and its
  referenced probes/logs. The initial missing-timestamp and HTTPS refusals are
  retained as diagnostics. All disposable jobs used `run-with-temp` and finished.
- No implementation acceptance remains incomplete. The external TSA is an
  intentional fail-closed network dependency. Publication, adoption, action
  discovery, platform story 26 and migration completion remain outside this
  acceptance. This implementation handoff performed no commit, push, fetch,
  release, hook enablement or production/machine trust change.


## Review Triage Log

| Finding | Verdict | Route | Evidence |
| --- | --- | --- | --- |
| Blind 1: PFX key containment on unqualified operating systems | medium | patch | NuGet CertificateProvider loads PFX with default key-storage flags; Microsoft documents the usual user-key default and separate in-memory flag. Windows can create key-container files outside private scratch. Restrict this qualified path to Linux before package work and document the boundary. |
| Blind 2: SDK signing intermediate outside inner job scratch | medium | patch | NuGet SignCommandRunner uses Path.GetTempFileName; current signing environment inherits the outer temp paths. Forced child cleanup can bypass its finally. Bind signing TMPDIR/TMP/TEMP to the owned private directory. |
| Blind 3: forwarded child survives direct-child SIGKILL | medium | patch | NuGetForwardingApp starts a second process, and Unix ProcessReaper runs during managed shutdown. subprocess.run unwinding kills only its immediate child. Terminate and observe the owned command tree before removing signing material. Shared root cause with Edge 1. |
| Blind 4: indefinite command from external timestamp dependency | maybe-false | defer (medium, unverified) | The wrapper has no independent deadline, but this review did not establish whether the installed SDK timestamp/chain transports can wait indefinitely; hosted jobs also have outer deadlines. Inspect exact SDK transport cancellation/timeouts or demonstrate a real stalled command before adding a new guard. |
| Blind 5: timestamp absence accepted by authenticate_candidate | false | reject | This private helper is called only after sign_candidates supplies the fixed required timestamper, whose actual refusal returns failure. No reachable missing-timestamp result from that signing call was shown; retained restore warnings-as-errors additionally rejects NU3027 before any consumer execution. Direct SDK verification semantics alone do not demonstrate the alleged workflow admission. |
| Blind 6: prerequisite version documentation | low | patch | The README names tools without their qualified versions. State the qualified Linux/OpenSSL3/SDK11 prerequisites. Unsupported tool commands already fail closed; speculative extra version-dispatch branches are unnecessary. |
| Blind 7: no real cryptographic qualification | false | reject | evidence/25/candidate-signing-sdk-probe.py and its hash-bound passing receipt execute20 actual SDK/OpenSSL commands, including wrong/altered/expired candidates. candidate-signing-timesheets-check.py runs all six actual strict restores/builds/executions. These are completed qualification, not fake-SDK claims. |
| Edge 1: forwarded signer lifetime after termination | medium | patch | Confirmed by the same SDK process forwarding and Unix reaper path as Blind3. Group only these two findings for one process-tree cleanup correction. |
| Verification1: same-name payload rewrite untested | medium | patch | Pre-verified mutation run removed the entry-digest comparison while all36 tests passed. The added-entry fake covers only inventory. Add a validly authenticated same-name rewrite case that fails through digest preservation. |


### Post-review verification

The five direct corrections are complete: Linux-only qualification, private
signing temp paths, complete command-group termination/reaping, same-name ZIP
payload mutation coverage and explicit tool prerequisites. Isolated SDK commands
also disable shared compilation. The lifetime correction was re-reviewed with
no material finding. The corrected source passed 38 tests under Python3.12,
the20-command real cryptographic probe and all six actual SDK11/net10 consumers.
DLL/PDB hashes remained unchanged and scratch/key cleanup was confirmed.
One unverified timeout follow-up was recorded separately; no audit/signature
policy was weakened. The signer code is already available on remote Builds main
through concurrent publication; exact hashes/revisions and final receipts are in
`../specs/spec-cicd/evidence/25/candidate-signing-summary.json`.

Projects remains independently blocked by its Folder-owner preparation proof.
The existing Folders-only substitute is already approved in spec17; its complete
retained gates are still red, so it does not authorize publishing that owner
change based only on focused adapter tests. No Platform26 implementation,
production hook, adoption or release was enabled by this signing work.
