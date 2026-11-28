# EventStore Story 2.14 hosted Tenants artifact access

**2026-11-28 — Hosted probe passed.** The EventStore workflow token downloaded Tenants artifact `15255150419` and verified both receipt files. Story 2.14 remains `in-progress`. [EventStore hosted run](https://github.com/Hexalith/Hexalith.EventStore/actions/runs/46128700993)

## Initial preflight

**2026-11-28 — Blocked before dispatch.** Hosted run URL unavailable. The registered EventStore completion workflow requires a bound transition request and owner approvals before it reads Tenants artifacts. It has no read-only probe mode. EventStore is pre-adoption, and the Story 20 approval covers product preparation with unchanged owned workflow bytes. The [CiCd EventStore proposal route](../../../../../docs/contracts-prerequisites/owner-routes.md) is fixed to the Contracts prerequisite. A CiCd-owned EventStore probe with the completion job's token and permissions needs an approved delivery route.

The local control used the CiCd-agent profile to download artifact `15255150419` from [Tenants run 46122156253](https://github.com/Hexalith/Hexalith.Tenants/actions/runs/46122156253), head `b5cce6f814e692f41c7c91ff6adbe6626d19fb38`. The 2,826-byte archive matched GitHub's SHA-256 `b712783bb7fb5c9c3c2bfa10382ed5eb83300870d6b18e98aff90aafb4fbe7e8` and contained exactly two nonempty, CRC-valid entries, `tenants-source-backend.json` and `tenants-source-catalog-result.json`. GitHub reported expiry at `2027-02-26T07:38:43Z`. Hosted `GITHUB_TOKEN` access remains unverified.

The requested standalone probe can omit story-completion approvals. A fresh check from EventStore using `run-with-temp python3 references/Hexalith.Builds/check.py` exited 1 with `[Errno 2] No such file or directory` for `.github/hexalith-ci.json`. The available pre-adoption verification substitute covers product changes with unchanged owned workflow bytes. The separate owner delivery route remains the blocker.

No approved fallback credential was confirmed. CiCd-agent received HTTP 403 from the EventStore repository and Hexalith organization secret metadata endpoints. The interactive maintainer readback returned HTTP 404 for both named endpoints, and the readable secret inventories did not list `PHASE4_TENANTS_READ_TOKEN`.

- Inspected EventStore main commit `737db0cf69a556b6cadb24d0f74534807ad47a89`, tree `630d40b79810218bc8e3ca561b8262de450d008a`.
- Completion workflow blob `f35f83d217bd289e098bfc6f692d423dd3bce063`, workflow ID `419552357`. Its job grants read access to Actions, contents, checks, issues and pull requests.
- CiCd owner route checked at commit `c31df42ac893e52c3b566083f7e410680e5e6cec`, tree `e890f88deaa2f88e5e9d4c9cf98e833b864849d0`, route document blob `97353d89faec1e589e051cd655067d0d081e9a61`.

Story 2.14 remains `in-progress`. No workflow change or release commit selection was made.

## Authorized branch-only probe

The maintainer authorized the dedicated branch and a probe-only substitute for the unavailable Builds checker. EventStore main has no committed `.github/hexalith-ci.json`. The branch uses its initial push as the trigger because GitHub manual dispatch requires the workflow on the default branch. [GitHub manual dispatch documentation](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-running-a-workflow)

- Dedicated ref `refs/heads/cicd/story-2-14-tenants-artifact-probe`. The only candidate delta is the added `.github/workflows/story-2-14-tenants-artifact-probe.yml` (mode `100644`, blob `930d2426f27dcb5301131cf8cc049d1ca70eba67`).
- Fresh EventStore base commit `737db0cf69a556b6cadb24d0f74534807ad47a89`, tree `630d40b79810218bc8e3ca561b8262de450d008a`. Candidate commit `0f4d1aaaf6796febbaa5451b7351b470f08a88cf`, tree `5d322f2b2dee5ad45734e2f1782bff7cb88c35e9`, single parent equal to the base. Recorded before remote delivery.
- The completion workflow is byte-identical at blob `f35f83d217bd289e098bfc6f692d423dd3bce063`. The probe uses the same `ubuntu-24.04` runner, `github.token` binding and five read permissions.
- Exact-range commitlint 21.2.4 passed using the EventStore lockfile blob `5ba2a83c6eada70d246eede11980210581e6327b` and config blob `ffe0164f2fa3655a94b31895f4fd02f42192d02b`. Output SHA-256 `e23b212d51cc73cb4768ab2fc53b44bc9c9839198a57f2304f737fe2fdf76408`.
- Actionlint 1.7.12 passed for the exact committed workflow using the Builds pin `aebabdadadffa108801992253c7910f37437b115` and verified release archive SHA-256 `8aca8db96f1b94770f1b0d72b6dddcb1ebb8123cb3712530b08cc387b349a3d8`. Output SHA-256 `cd00674dbf500ba8b883ded8ecdfe563cf6aa143c14f706d0b8f7e7fa88cc657`.
- All 23 baseline workflow events and branch filters exclude this push. The release workflow (blob `e08272bff06157faaa7964215c5ff01de1024ecd`) is dispatch-only, and the untouched release guard rejected the exact probe ref with exit 1. Contracts publication and OCI attestation require `main`. Trigger/permissions check SHA-256 `32524cb9df70f50abed1f60f8b2515aa6b3ffe0e1b05855b36258635e18e0242`, release guard output SHA-256 `e95232722e78a2de367d99f99f67462d856bbc9f1dd7ea616d2026dc7902224f`.
- The exact committed Bash step passed a local positive control using the configured CiCd-agent read identity (HTTP 200 after one redirect). Output SHA-256 `85c4e9bed3022eef269d81f584f0d12571df218f02cf1a06e709d2894a8f9339`.

### Hosted delivery and result

- The interactive maintainer pushed the exact candidate as a new branch with a creation-only lease and no tags. Remote readback verified the candidate on that branch and the same `main` commit.
- GitHub scheduled exactly one run for the candidate, [EventStore run 46128700993, attempt 1](https://github.com/Hexalith/Hexalith.EventStore/actions/runs/46128700993), via `push`. Its probe job is `140928916468`. The input was Tenants artifact `15255150419` from [Tenants run 46122156253](https://github.com/Hexalith/Hexalith.Tenants/actions/runs/46122156253).
- The GitHub-hosted `ubuntu-24.04` job completed successfully at `2026-11-28T09:05:19Z`. The artifact endpoint returned HTTP 200 after one redirect. The ZIP matched SHA-256 `b712783bb7fb5c9c3c2bfa10382ed5eb83300870d6b18e98aff90aafb4fbe7e8`. It contained exactly `tenants-source-backend.json` and `tenants-source-catalog-result.json`, both nonempty and CRC-valid. The three normalized status lines have SHA-256 `85c4e9bed3022eef269d81f584f0d12571df218f02cf1a06e709d2894a8f9339`. [Hosted probe job](https://github.com/Hexalith/Hexalith.EventStore/actions/runs/46128700993/job/140928916468)
- The successful built-in-token run leaves the completion verifier and approval gates intact. Post-run readback confirmed the same EventStore main revision and `in-progress` sprint status.
