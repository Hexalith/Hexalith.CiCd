# Story 26 prerequisite source qualification

The source candidate implements authenticated historical Builds preparation,
finite compatibility project orchestration and strict public NuGet verification.
All 269 selected suite tests passed, plus the final focused ZIP-reencoding probe. This is local source qualification; no central
release, immutable released source selection, Platform adoption or CAP-16 result
is claimed.

The original CiCd/Builds baselines are respectively
`9c2a65cbf1d523609000fffb525fba5cf5e8b4b3` and
`05bda4e01d70afacb5048d5c336f383a301c0974`. Another workspace session advanced
HEADs during implementation to CiCd
`4d5a41c69b1c57e049a3d3a5c084259d896c6e5b` and Builds
`d54075d6e9d9eb1c41827fe5ef39a9df3100b2ee`, committing pending source work.
Those commits were preserved. `prerequisite-verification.json` captures exact
working-file SHA-256 values, observed HEADs, executed commands, log hashes and
source boundaries. `prerequisite-builds.patch` and `prerequisite-cicd.patch`
compare the selected implementation paths from the original baselines to the
qualified working bytes, including changes now committed by the other session.
Untracked planning records are included by hash. Concurrent unrelated product
and evidence changes were preserved.

## Executed checks

Every disposable job used `run-with-temp`. Logs are the adjacent
`prerequisite-<name>.txt` files; JSON records each exact command and working
directory. Tests ran on Python 3.14.4, with .NET SDK 10.0.404 for the six-case
isolation fixture and the repository fixture's own pinned SDK for release tests.

| Suite | Tests | Result |
| --- | ---: | --- |
| New focused prerequisite cases | 14 | Passed |
| Final signature/body ZIP-reencoding probe | 1 | Passed |
| Schema and strict CI reader | 23 | Passed |
| Existing preparation lifetime | 10 | Passed |
| Shared CI pipeline | 40 | Passed |
| Local checker | 38 | Passed |
| Real release-build discovery, pack and audit preservation | 3 | Passed |
| Authenticated draft artifact reader | 27 | Passed |
| Existing release publisher | 17 | Passed |
| CiCd renderer | 44 | Passed |
| CiCd validator | 53 | Passed |

The pipeline and release regression logs intentionally contain controlled
product test/audit failures. Their enclosing tests require those refusals; each
suite's final unittest result is successful. No audit, analyzer or test gate was
weakened. An initial focused run found a bounded-stream adapter error and an
unavailable import diagnostic mismatch; both were fixed before the final
14-case qualification. The schema test's allOf default inspection was extended
to handle additive nonconditional schema constraints.

## Matrix coverage

Case names below refer to `Github/lib/tests/test_platform_support.py` in Builds.

| Required state | Executed evidence |
| --- | --- |
| Options absent/null and unchanged defaults | `ContractTests.test_defaults_closed_fields_and_semantic_refusals`; `StrictPackageTests.test_legacy_manifest_and_legacy_verification_have_no_new_policy`; existing schema/preparation/draft/publisher regressions. |
| Historical producer and different active catalog | `HistoricalTests.test_independent_catalogs_historical_bytes_and_one_lifetime` creates two actual Git commits/tags with different catalog blobs/digests and authenticates each independently. |
| Preparation before first evaluation in CI/local/release | `HistoricalTests.test_ci_local_and_release_prepare_before_first_evaluation` executes all three real entry-point routes with controlled product commands and asserts the required assembly exists at first evaluation. |
| Wrong, unsigned, changed or unavailable producer | `HistoricalTests.test_wrong_changed_unsigned_unavailable_producers_export_nothing` exercises digest, authority, signature-verifier, Tooling, host and full executable identity failures; each exports nothing and removes private scratch. |
| Reuse and changed source/input bytes | `HistoricalTests.test_source_binding_tool_and_active_identity_revalidated` and `test_job_reuse_prepares_once_and_mapping_conflicts_fail`; existing preparation tests cover changed generated import bytes and caller environment restoration. |
| Closed official handoff authority | `HistoricalTests.test_official_markers_run_tag_manifest_and_closed_binding_refuse_changes` tests changed release body, wrong tag source, failed original run, candidate authority, foreign producer and altered bound manifest. |
| Six exact selections and real output isolation | `DeclaredProjectTests.test_real_sdk_six_exact_selections_and_disjoint_outputs` performs actual restore/build for 3.130.0, 3.130.1, 3.130.2, 3.132.1, 4.1.0 and 4.2.0. Each observed MSBuild version matches the selection; each private artifacts tree has its own DLL/assets; source `bin/obj` remain absent. |
| Unsafe, foreign, uncommitted, symlink or policy-changing case | `DeclaredProjectTests.test_uncommitted_foreign_symlink_policy_import_and_test_inputs_fail`; contract tests reject unknown version properties, hidden command fields, duplicate IDs/selections, too many cases and unsupported platform jobs. |
| Case failure stops successors and preserves release audits | `DeclaredProjectTests.test_failure_stops_successors_and_retains_release_policy` preserves the exact release flags/targets, returns the actual product exit code and observes no successor restore/build. The real release regression requires NU1903 to suppress payload finalization. |
| Cases stay outside package discovery | `StrictPackageTests.test_real_evaluated_opt_in_opt_out_and_discovery_exclusion` verifies declared auxiliary paths are excluded from evaluated release discovery. Root-solution tests retain the existing shared classification paths. |
| Evaluated opt-in and unchanged false/empty opt-out | The same real SDK evaluation/pack case exercises empty, `false`, `False` and `true`, confirms legacy manifest keys when false, authenticates the true boolean policy entry and rejects inconsistent TFM policy. A literal JSON false manifest policy is refused because opted-out entries must omit the key. |
| Public-only signature/ZIP difference passes | `StrictPackageTests.test_authenticated_manifest_round_trip_and_strict_public_payload` authenticates original artifact bytes/policy, then verifies an archive differing by the root signature with an explicitly controlled successful signature subprocess. |
| Public body/signature failures block publication | The same case rejects changed, added, removed, unsafe and duplicate member bodies, unsigned archives and a failing signature verifier. `test_real_dotnet_rejects_invalid_signature` executes the actual bounded `dotnet nuget verify --all` refusal. |
| Credential isolation and no publisher module callbacks | Focused producer/publication process controls assert credential-free environments and private working directories; existing publisher regressions exercise the actual authenticated handoff/composite. No module callback, source rebuild, repack or extra publisher was added. |
| Tagged renderer/validator agreement | New renderer/validator fixtures create synthetic local Git-object contracts containing the matching candidate schema/reader; defaults and valid inputs round-trip, invalid version/policy inputs fail, and production `builds-version` remains unchanged. |

## Qualification boundary and remaining work

Historical archive and executable bytes are deliberately synthetic controls in
these protocol tests. Successful cryptographic verification is controlled; the
invalid-signature refusal runs the actual SDK verifier. The real six-case probe
uses small nonshipping projects and observes version properties and output
isolation; it does not qualify Platform's genuine package graphs or product
assertions. Source success therefore does not grant Platform adoption.

The existing authorized central release process must publish and qualify an
acceptable immutable bot-authored exact Builds tag/source. Genuine Platform
historical signed producer, all six compatibility package cases and public
package payload/signature qualification remain required before story 26 consumes
the release. Production pins, setup registrations, rendered modules and Platform
source were not changed by this implementation. No repository remote operation
was performed. Independent review remains the parent workflow's next step.
