---
title: 'Resolve five deferred Builds invocation and attachment findings'
type: 'bugfix'
created: '2026-11-23'
status: 'done'
route: 'oneshot'
---

<frozen-after-approval reason="requested batch">

## Intent

**Problem.** Shared CI can misread a valid solution name as an option, and release configuration errors can name a temporary file. Attachment verification still needs one independent environment identity case. Two related findings have upstream fixes that need to be verified and recorded.

**Approach.** Resolve DW-7, DW-15, DW-16, DW-18 and DW-25. Use a resolved module-contained solution path for the SDK, report the committed configuration path in release errors, and verify that an otherwise valid attached capture refuses a descriptor from another environment. Verify the existing candidate-policy refusal and README guidance against Builds main. Publish the verified changes and record the results in the CiCd ledger.

</frozen-after-approval>

## Implementation Notes

- Builds base `443c48bb497ec45f6fc1ac3f30e25860d1eb3fed`.
- `restore_and_build` uses the same contained solution path resolver as project discovery. The command regression covers a leading dash and a space in the same filename.
- `dispatch_settings` reports the repository-relative configuration path. It follows the existing expected-state loader's convention for errors from Git blobs. The composite regression checks repeat stability and the absence of configuration outputs for malformed input.
- The attached-routing theory changes only the descriptor environment and checks the identity diagnostic. The positive owner and attachment controls still compare exact retained bytes. The native executor fixture marks its own root so an ancestor Git marker cannot redirect manifest file validation.
- Builds `565b9e63bce9d3b5b43483d01da81ef7ceb33a20` added the isolated candidate-policy case and corrected the README section, attachment semantics and port retry guidance. Both are present on the selected Builds base.

## Review Triage Log

- Medium, patched. Keep the configured relative solution for discovery and use the resolved path for SDK restore and build. The additional-test fixture exercises both discovery and restore/build.
- Low, patched. Invalid release configuration emits only the selected source identity and mode. Repeat the composite run under a temporary path containing a tab to verify the diagnostic uses the committed path after escaping.
- Low, patched. An invalid dispatched Builds sample keeps the full sample directory in the error. The complete-draft case reaches dispatch configuration validation without a create-mode comparison.
- Low, verified. A real .NET 11.0.100 run produced `MSB1001` for the raw leading-dash solution filename and restored and built the identical solution through the shared entry point.
- Medium, patched. The first focused attachment replay stopped at manifest validation because `/tmp/.git` redirected relative paths out of the fixture. An explicit fixture root follows the existing composition test convention. Manifest validation failures now include the underlying diagnostic messages.
- Low, deferred. Existing `tests.additional` restore and build commands can still pass a leading-dash project filename as an SDK option. The ledger records the separate input path.
- Low, patched. The CiCd ledger records each disposition, and the verification section identifies the Builds publication source.

## Verification

- Builds `main` was verified at source `c3668b07b070fa7aaa919030a6ba434ec342d2bf`, tree `2687b1993883c6ad36eb1e6ba2d43e686ef45a32`. Its parent is the concurrent catalog authority change `641dd5e47ced09389ae0698d9eee34befcc45a5c`.
- The .NET 11.0.100 Release build finished with zero warnings and errors. All 11 focused routing and candidate-policy cases passed on the combined source. Build log SHA-256 `de1e889f7b3b63e6f9cc7ffa132719c2a6bfb5c1a805d252eb3fef1c10c21773`. Test log SHA-256 `ba1786d1b406931e40dca1352a09e51eaac9d9c00ad5f039ed7b23bec952678c`.
- All 15 release adapter tests passed. Log SHA-256 `aa3d2074126f452c6b1fb5280bc21739ac96e490dc11871c4aab2f1c0ba44ae6`.
- All 39 subprocess pipeline tests passed. Log SHA-256 `f3f4cfa19b40697afe59ae6ca82a326059e6d6a516324816a18bd5017814aa9a`.
- The shared CI suite ran 53 tests and passed 52. Its real coverage-report test returned exit 7 because the .NET test host tried to write to a read-only home directory. The same test failed on the pulled Builds baseline with the same write error. Candidate suite log SHA-256 `c0c87eebfa5a358c2f4b0321cc8d6a71b10b1ed37ee17d246b7850922bf12dae`. Baseline replay log SHA-256 `d2c6ab91d50b6dd64b94eac587f9a2cc6be17de74cc4c0b7a488ca20e7941ead`.
- All eight CiCd evidence checker tests passed. Commitlint 21.2.4 accepted both exact commit messages with zero warnings.
