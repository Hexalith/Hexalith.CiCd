---
title: '21 prerequisite: frozen release timestamp'
type: 'feature'
created: '2026-11-19'
status: 'in-review'
route: 'dispatch'
baseline_commit: '72a1332c07672f1bd174d58b5d6e1d564c1c6cbb'
builds_baseline_commit: 'a8e2ae292a45070e95646bf6db8a7f7a8704c1d3'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/implementation-artifacts/prerequisite-21-frozen-release-timestamp.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The shared release build never sets `ContainerProvenanceCreated`, which EventStore and Parties container targets require, and the SDK stamps each platform image with its own clock. Parties adoption needs one publisher-owned created instant across every project, image and runtime identifier.

**Approach:** Capture one UTC second at the start of `build_release`, pass it as Builds' existing generic `ContainerProvenanceCreated` property to every SDK command, bind every image's `org.opencontainers.image.created` label to it and verify it in the payload. It ships later through the central Builds release and CiCd pin bump; story 21 consumes it.

## Boundaries & Constraints

**Always:** One authority: the publisher clock read once per `build_release`, validated as an exact UTC RFC 3339 second with a real calendar date. Reuse existing names and patterns. Keep `release-manifest.json` keys, complete-mode original-artifact reuse and three-argument `release_flags` callers unchanged. Edit Builds in `references/Hexalith.Builds` on a branch from freshly fetched `main` (`a8e2ae292a45070e95646bf6db8a7f7a8704c1d3`). Use `run-with-temp` for disposable work.

**Never:** No new workflow or composite input, environment override or alternate time source (commit time, per-project or per-RID clocks). No module-name branches; no Parties, EventStore or Tenants edits. Do not rewrite SDK config `created`/history or child manifest digests. Do not weaken existing label, archive or audit checks. No push, release, pin bump, registration or adoption in this work.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Multi-RID containers | Real fixture with two platforms; clock advances on every read | Every child config's `image.created` (and `artifact.created` when present) equals the first instant; clock read once | N/A |
| Package-only or `solution: none` | No container project | Same packages and manifest as today; `none` still runs no SDK command | N/A |
| Plain consumer | Container without its own provenance targets | Label carries the publisher instant; no extra configuration | N/A |
| Invalid instant | Fraction, offset, or impossible date such as `2026-02-30T00:00:00Z` | Rejected before any SDK command; no payload | `PipelineError` |
| Label mismatch | Child created label differs from the instant or between platforms | Inspection fails; no manifest written | `OciError` |
| Complete mode | Stored original payload | Publishes original bytes and labels without rebuilding | N/A |

</frozen-after-approval>

## Code Map

Builds paths are relative to `references/Hexalith.Builds/`.

- `Github/lib/release_build.py:46` `release_flags` -- shared flags; already disables SDK revision/version labels. Keep its signature (`tests/test_platform_support.py:516,659`).
- `Github/lib/release_build.py:195` `build_release` -- capture point; `flags` already reach discovery, restore, build, pack and each RID publish.
- `Github/release-build/release.targets` `HexalithReleaseLabels` -- extend its Remove/Include label pattern.
- `Github/lib/oci_archive.py` `inspect_files`, `inspect_archive:214`, `combine_archives:220` -- add optional `created`; `release_draft.py:360` and `release_publish.py:278` callers unchanged; `release_draft.py:326` requires exact manifest keys.
- `Props/ContainerProvenance.targets`, `Github/publish-containers/{publish-containers.sh:30,212,oci_registry_validator.py:504}` -- existing name, single capture and format rule (regex plus `strptime`); reuse the rule, do not import legacy code.
- `Github/lib/tests/test_release_build.py:274` -- real SDK fixture (`test/fixtures/release`, `Release.slnx`, linux/amd64 and arm64); also `test_release_oci.py`, `test_release_complete.py`.

## Tasks & Acceptance

**Execution:**
- [x] `_bmad-output/planning-artifacts/architecture/architecture-cicd-2026-11-07/ARCHITECTURE-SPINE.md:416` (CiCd) -- add the publisher-created rule to the build bullet -- record the contract before runtime edits.
- [x] `Github/lib/release_build.py` -- add a validated publisher-instant helper with an injectable clock; in `build_release` append `-p:ContainerProvenanceCreated=<instant>` and `-p:ContainerGenerateLabelsImageCreated=false` to `flags` and pass the instant to archive combine/inspect -- one authority for all SDK calls.
- [x] `Github/release-build/release.targets` -- when the property is non-empty, Remove and Include `org.opencontainers.image.created` -- consistent label for every image.
- [x] `Github/lib/oci_archive.py` -- with `created`, require each child's `image.created` to equal it and `artifact.created`, when present, to match -- payload-level proof.
- [x] `Github/lib/tests/test_release_build.py`, `test_release_oci.py` -- cover every matrix row with controlled clocks and fixture archives, no sleeps -- matrix coverage.
- [x] `Github/release-build/README.md` (new), `README.md` composite list -- document the property, time authority, format and scope -- consumer interface.
- [x] `_bmad-output/specs/spec-cicd/evidence/21/frozen-created/` (CiCd) -- record exact Builds revision, test results and digests -- evidence rule.

**Acceptance Criteria:**
- Given unchanged consumers and callers, when the full Builds Python contract suite runs, then it passes with no skipped or removed assertions.
- Given a fixture container project that requires `ContainerProvenanceCreated` with no default, as EventStore and Parties do, when the release publishes it, then the property equals the publisher instant without product changes.

## Implementation Notes

- Builds branch `feat/frozen-release-created` from `a8e2ae29` was pushed at `7f085bad76da517d85b835f45facd649dfc7bc36` at the user's request. The commit matches the qualified tree and blob IDs in [the verification record](../specs/spec-cicd/evidence/21/frozen-created/verification.json).
- `build_release(..., clock=utc_second)` is the injectable clock; `publisher_created` validates it (regex plus `strptime`) before the payload directory or any SDK command exists.
- With `ContainerGenerateLabelsImageCreated=false` the SDK emits neither created label, so plain consumers carry `image.created` only; `artifact.created` exists only when a product declares it, and must match.
- `oci_archive` `created=""` keeps draft, publish and complete readers unchanged; only the build passes the instant.
- AC1 locally: 15/16 suite groups passed in the original clean clone (`Github/lib/tests` 783 OK, no skips). The remaining group's token-gated online policy test passed on the exact committed tree in a separate 14-test workflow policy run. The authenticated `actionlint` and `zizmor` workflow audit passed on that same tree. Hosted Builds CI remains pending.

## Spec Change Log

## Review Triage Log

## Design Notes

- **Name:** the prerequisite left it open. `ContainerProvenanceCreated` is Builds-owned, the legacy publisher passes it once per release, EventStore and Parties require it and Tenants imports Builds' targets, so story 21's mapping becomes identity.
- **Scope is labels:** this matches the legacy validator. The SDK's fractional config `created` stays as written, because rewriting it would change the child digests that `combine_archives` keeps unchanged.
- **Universal label:** the release already rebinds source/revision/version for every image, and `created` follows suit. Modules without their own targets get a consistent value with no setup.

## Verification

**Commands (from `references/Hexalith.Builds`):**
- `run-with-temp python3 -m unittest discover -s Github/lib/tests -p 'test_release_*.py'` -- expected: all pass, including the real SDK container graph.
- `run-with-temp uv run --no-cache --locked --script --python 3.12 Tools/ci/run_python_tests.py` -- expected: full contract suite passes.
- `python Tools/ci/lint_workflows.py --export-path` -- expected: clean.
