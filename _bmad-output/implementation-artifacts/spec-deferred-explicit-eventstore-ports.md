---
title: 'Resolve five deferred explicit EventStore port findings'
type: 'bugfix'
created: '2026-11-23'
status: 'done'
route: 'oneshot'
---

<frozen-after-approval reason="human-owned intent">

## Intent

**Problem.** Malformed or incompatible explicit EventStore port requests need precise refusal coverage. An unmanaged occupied port loses the endpoint in its diagnostic. The allocation tests can miss a duplicate endpoint and rely on reusing ports from the OS ephemeral range.

**Approach.** Resolve DW-13, DW-17, DW-19, DW-20 and DW-21 in Hexalith.Builds. Use valid manifests to verify CLI and service refusals before startup. Retain the endpoint in the unmanaged bind diagnostic and verify claim cleanup. Make the allocator's explicit-port exclusion observable independently of its in-process history. Use the non-ephemeral allocator for the successful explicit-port test and keep the unmanaged listener bound throughout the refusal test.

</frozen-after-approval>

## Implementation Notes

- Builds base `4adecfe2af4758aa66039a1221de20774ca56e87`. The CLI keeps `HXC001` and adds a fixed option-conflict explanation. The execution service still reports `HXC002` for invalid direct calls.
- The allocator carries the exact endpoint through a bind failure. The engine reports it under `HXR020` and runs bounded teardown. Managed claims still use `HXR031` and identify their owner.
- The exclusion regression checks the actual input passed to independent allocation. The success fixture gets its port from the normal allocator. The occupied fixtures keep their listeners bound through refusal.

## Review Triage Log

- Low, recorded limitation. The allocation test independently observes deletion of the requested-port exclusion at its handoff to the allocator. A deterministic test of the general allocator's candidate filtering would require a separate candidate seam.
- Medium, patched. The typed endpoint failure retains both errors if the initial claim rollback fails, and bounded teardown retries release.
- Low, patched. The README limits the endpoint diagnostic to a failed pre-launch probe.
- Medium, patched. The unmanaged CLI regression checks the diagnostic field, claim release and removal of the failed run workspace.
- Medium, patched. The rollback fixture verifies an unrelated prior owner's claims survive.
- Low, patched. Malformed requests use a validated declaration, and the attachment assertion uses the existing valid suite and live owner fixture.

## Verification

- Published Builds source `443c48bb497ec45f6fc1ac3f30e25860d1eb3fed` and tree `8473fb8d50a9aa14a7d658d68db4a37ab2fe74dc`. The remote `main` ref was verified at that commit.
- The .NET 11.0.100 build of `Hexalith.Builds.Module.Tests.csproj` finished with zero warnings and zero errors. All 27 focused tests passed. The local restore used the committed signer configuration with offline revocation checking because the sandbox could not reach the revocation servers.
- Build log SHA-256 `876d5c5ef5a35ab2b13292dd729f5a8237177ad7aabd217e75784406edd78982`. Test log SHA-256 `a248fd0fd55e5a891403e0d635717f724a9db035c95eea28e2c4bfbc35b1103e`.
- All eight CiCd evidence checker tests passed. The pinned commitlint 21.2.4 accepted both publication messages.
