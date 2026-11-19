---
title: '21 prerequisite: frozen release timestamp'
type: 'feature'
created: '2026-11-19'
status: 'done'
route: 'dispatch'
baseline_commit: '72a1332c07672f1bd174d58b5d6e1d564c1c6cbb'
builds_baseline_commit: 'a8e2ae292a45070e95646bf6db8a7f7a8704c1d3'
review_loop_iteration: 1
builds_fix_base_commit: '7f085bad76da517d85b835f45facd649dfc7bc36'
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
- `Github/release-build/release.targets` `HexalithReleaseLabels` -- extend its Remove/Include label pattern to both created labels. SDK 10.0.403 `Microsoft.NET.Build.Containers.targets:152` generates `image.created` and `artifact.created` from the single switch `ContainerGenerateLabelsImageCreated`.
- Builds `main` `7f085bad76da517d85b835f45facd649dfc7bc36` (tree `2361676d…`) already holds the first implementation. The forward fix below changes only its delta.
- `Github/lib/oci_archive.py` `inspect_files`, `inspect_archive:214`, `combine_archives:220` -- add optional `created`; `release_draft.py:360` and `release_publish.py:278` callers unchanged; `release_draft.py:326` requires exact manifest keys.
- `Props/ContainerProvenance.targets`, `Github/publish-containers/{publish-containers.sh:30,212,oci_registry_validator.py:504}` -- existing name, single capture and format rule (regex plus `strptime`); reuse the rule, do not import legacy code.
- `Github/lib/tests/test_release_build.py:274` -- real SDK fixture (`test/fixtures/release`, `Release.slnx`, linux/amd64 and arm64); also `test_release_oci.py`, `test_release_complete.py`.

## Tasks & Acceptance

**Execution:**
- [x] `_bmad-output/planning-artifacts/architecture/architecture-cicd-2026-11-07/ARCHITECTURE-SPINE.md:416` (CiCd) -- add the publisher-created rule to the build bullet -- record the contract before runtime edits.
- [x] `Github/lib/release_build.py` -- add a validated publisher-instant helper with an injectable clock; in `build_release` append `-p:ContainerProvenanceCreated=<instant>` and `-p:ContainerGenerateLabelsImageCreated=false` to `flags` and pass the instant to archive combine/inspect -- one authority for all SDK calls.
- [x] `Github/release-build/release.targets` -- when the property is non-empty, Remove and Include `org.opencontainers.image.created` and `org.opencontainers.artifact.created` -- consistent labels for every image. (Review 1 found that the first implementation rebinds only `image.created`; see the forward fix.)
- [x] `Github/lib/oci_archive.py` -- with `created`, require each child's `image.created` to equal it and `artifact.created`, when present, to match -- payload-level proof.
- [x] `Github/lib/tests/test_release_build.py`, `test_release_oci.py` -- cover every matrix row with controlled clocks and fixture archives, no sleeps -- matrix coverage.
- [x] `Github/release-build/README.md` (new), `README.md` composite list -- document the property, time authority, format and scope -- consumer interface.
- [x] `_bmad-output/specs/spec-cicd/evidence/21/frozen-created/` (CiCd) -- record exact Builds revision, test results and digests -- evidence rule.

**Forward fix (review 1), on a branch `fix/frozen-release-artifact-created` from freshly fetched Builds `main` `7f085bad`:**
- [x] `Github/release-build/release.targets` -- in `HexalithReleaseLabels`, when `ContainerProvenanceCreated` is non-empty, Remove and Include `org.opencontainers.artifact.created` with the instant, alongside `image.created`; update the comment -- plain consumers keep both created labels.
- [x] `Github/lib/tests/test_release_build.py` -- the real multi-RID test asserts that both created labels equal the instant for every child of both containers, including the plain one -- matrix rows 1 and 3.
- [x] `Github/lib/tests/test_release_complete.py` -- drop the `release_build.build_release`/`publisher_created` patches, which no complete path imports, and their comment; keep the byte and label assertions -- no dead guards.
- [x] `Github/lib/release_build.py` -- make the `strptime` failure message "release created instant must be a real UTC date and time" -- hours, minutes and seconds out of range are not calendar errors.
- [x] `Github/release-build/README.md` -- state that the release rebinds both created labels for every image; remove "appears only when the product declares one" -- consumer interface.
- [x] `ARCHITECTURE-SPINE.md` (CiCd) -- the build bullet names both created labels, says the build phase (`release_build.py --phase build`) reads the clock, marks the rule "pending central Builds release", and frontmatter `updated` is bumped -- truthful contract.
- [x] `_bmad-output/specs/spec-cicd/evidence/21/frozen-created/artifact-created-fix.json` (CiCd, new) -- record the fix base commit and tree, the candidate tree and blob ids, the CiCd baseline commit and tree, the spec blob, `recorded_at` as a UTC time, each digest with its exact command (`git diff --full-index`), and the mutation result with its log digest; leave `verification.json` unchanged -- evidence rule.
- [x] Implementation Notes (this spec) -- replace the note "plain consumers carry `image.created` only" with the fixed behavior.

**Acceptance Criteria:**
- Given unchanged consumers and callers, when the full Builds Python contract suite runs, then it passes with no skipped or removed assertions.
- Given a fixture container project that requires `ContainerProvenanceCreated` with no default, as EventStore and Parties do, when the release publishes it, then the property equals the publisher instant without product changes.

## Implementation Notes

- Builds branch `feat/frozen-release-created` from `a8e2ae29` was pushed at `7f085bad76da517d85b835f45facd649dfc7bc36` at the user's request. The commit matches the qualified tree and blob IDs in [the verification record](../specs/spec-cicd/evidence/21/frozen-created/verification.json).
- `build_release(..., clock=utc_second)` is the injectable clock; `publisher_created` validates it (regex plus `strptime`) before the payload directory or any SDK command exists.
- With `ContainerGenerateLabelsImageCreated=false` the SDK emits neither created label, so `release.targets` rebinds both: every image, plain consumers included, carries the instant as `image.created` and `artifact.created`. Inspection still requires `artifact.created`, when present, to match.
- `oci_archive` `created=""` keeps draft, publish and complete readers unchanged; only the build passes the instant.
- AC1 locally: 15/16 suite groups passed in the original clean clone (`Github/lib/tests` 783 OK, no skips). The remaining group's token-gated online policy test passed on the exact committed tree in a separate 14-test workflow policy run. The authenticated `actionlint` and `zizmor` workflow audit passed on that same tree. Hosted Builds CI remains pending.
- Forward fix: Builds branch `fix/frozen-release-artifact-created`, fast-forwarded onto `main` `74e6e4b5`, holds candidate tree `eae30aa4c9a93e449c97f585bdb3ff416881e45d`, uncommitted and unpushed ([fix record](../specs/spec-cicd/evidence/21/frozen-created/artifact-created-fix.json)). On the earlier candidate tree `1f81f3fc` (base `7f085bad`), release tests passed (218 OK, no skips) and the full suite passed 15/16 groups in a disposable clone (`Github/lib/tests` 783 OK, no skips). The release route of the platform cohort test now requires the instant on every declared-build evaluation and command. Without a GitHub token, the token-gated online zizmor test and the online zizmor audit remain open. Restoring the `7f085bad` `release.targets` fails the real multi-RID test on the plain container's missing `artifact.created`.
- Forward fix committed locally as Builds `192d1a13d5f09b6b9569dbd977a09dc6da76e0e6` (tree `eae30aa4`, parent `74e6e4b5`) on `fix/frozen-release-artifact-created`, not pushed; its message passed pinned commitlint 21.2.4. On that tree: release tests 218 OK; the clean-clone suite passed 15/16 groups (`Github/lib/tests` 783 OK, no skips), and the remaining group fails only on the token-gated online zizmor test; actionlint passed. Builds `main` must not be released until this lands (`release_blocker` in the fix record).
- Pushed to Builds `main` as `99baf1dbf2dc2c098ea758f16e4e9bacc892ad7a` (tree `45868ad6`) after rebasing onto `5a4de003`. All six fix blobs are unchanged; release and cohort tests passed on the intermediate rebase tree `68940027`. Hosted Builds CI on `99baf1db` is pending.

## Spec Change Log

- **Review 1, loop 1 (2026-11-19).**
  - **Trigger:** triage rows 1 and 2. `-p:ContainerGenerateLabelsImageCreated=false` turns off both SDK created labels, but `release.targets` rebinds only `image.created`, so plain consumers lose `org.opencontainers.artifact.created`.
  - **Amended:** Code Map (`release.targets`, fix base), release.targets task text, a new forward-fix task list, Design Notes (universal and both-labels).
  - **Fix route:** the human chose a forward fix because `7f085bad` already reached Builds `origin/main`; nothing is reverted.
  - **Known-bad states to avoid:**
    - a release image without `artifact.created`;
    - test patches on symbols that no production path imports;
    - calendar-date messages for time-of-day errors;
    - spine contracts written in the present tense before central release;
    - evidence without CiCd commit and tree ids, spec blob, UTC time or digest commands.
  - **KEEP:** everything else in `7f085bad`:
    - `utc_second`/`publisher_created` (regex plus `strptime`);
    - `build_release(..., clock=utc_second)`, which reads the clock first, before the payload directory;
    - the two appended flags and the unchanged `release_flags`;
    - `oci_archive` `created=""` and `OCI created label mismatch`;
    - `AdvancingClock`, `recorded()`/`assert_one_instant`, `INVALID_INSTANTS`;
    - the `Provenance` fixture that requires the property with no default, and its negative publish;
    - the fixture-archive mismatch tests, the `sdk_archive(labels=)` parameter and complete-mode byte equality;
    - the README structure and the `verification.json` layout.
  - **Verification environment:** the shared checkout's `node_modules` is stale. Run the full suite in a disposable clone after `npm ci --ignore-scripts` and `lint_workflows.py --install-only`. If no GitHub token is permitted, report the token-gated test and the online zizmor audit as open; do not work around them.

## Review Triage Log

Review 1 (diff `a8e2ae29..2361676d` plus CiCd spine and evidence; layers: blind, edge-case, verification-gap).

| # | Finding | Verdict | Route | Evidence |
|---|---------|---------|-------|----------|
| 1 | Release turns off both SDK created labels but rebinds only `image.created`, so plain consumers lose `org.opencontainers.artifact.created` | medium | bad_spec (A) | SDK 10.0.403 `Microsoft.NET.Build.Containers.targets:152`: one switch generates both labels. The prerequisite requires existing consumers to keep current behavior and all created labels to carry one instant. `Props/ContainerProvenance.targets` rebinds both. Task 3 named only `image.created`. |
| 2 | An inherited base-image `artifact.created` is no longer overwritten, so the release fails with a mismatch | maybe-false | bad_spec (A) | Same root cause as 1. Unverified whether any module base image carries the label; the fixture's `runtime:10.0-alpine` does not. |
| 3 | Children may disagree on whether `artifact.created` is present | low | rejected | Needs RID-conditioned label items, which is unlikely; the fix adds a cross-child guard. |
| 4 | Isolated preflight `dotnet msbuild` runs without the instant | false | rejected | `build_projects.preflight` never received release flags. It is the CI adapter-shape and source-mapping check that module CI runs without the property. `build_declared` re-runs it with release flags, and it produces no payload. |
| 5 | Spine says the `build` job reads the clock "at its start", although checkout, prepare and SDK setup precede it | low | patch (moot: loopback) | The README correctly names `--phase build`. |
| 6 | Evidence implies the full suite passed | false | rejected | `verification.json` records 14/16 and 15/16 groups and lists the token-gated test as open. |
| 7 | Complete-mode test patches `release_build.build_release`/`publisher_created`, which no complete path reaches | low | patch (moot: loopback) | No `Github/lib/*.py` module imports `release_build`. Byte equality is the real proof, so the fix is a deletion. |
| 8 | AC2 fixture differs from Parties targets; malformed values are untested at the product boundary | false | rejected | The release passes only a validated instant as a global property, so target ordering cannot change the value. Single-RID publication does not use `_PublishMultiArchContainers`, and the release cannot produce malformed values. |
| 9 | Spine states the rule as current without "pending central release" and leaves `updated` unbumped | low | patch (moot: loopback) | Spine convention at `ARCHITECTURE-SPINE.md:850,879` marks unreleased prerequisite contracts. |
| 10 | Evidence does not say how `candidate_patch_sha256` was computed; the ad hoc script exists only as a digest; the mutation has no digest | low | patch (moot: loopback) | The digest reproduces only with plain `git diff`; `--full-index` gives a different value. |
| 11 | Evidence lacks the CiCd baseline commit and tree, the spec blob, and a time in `recorded_at` | low | patch (moot: loopback) | AGENTS.md Evidence requires commit, tree and blob ids. |
| 12 | Test helpers duplicate the child walk and patch module globals | low | rejected | No named harm; the fix adds parameters. |
| 13 | Hour 24, minute 60 and second 60 are reported as "must be a real calendar date" | low | patch (moot: loopback) | These pass the regex and fail `strptime`; the fix is a message correction. |

Loopback A is on hold: tree `2361676d` was committed as Builds `7f085bad` and reached `origin/main` (`v6.3.4-1`) during review, so reverting local code no longer applies. The human chose the forward fix recorded in the change log.

Review 2 (diff `a8e2ae29..` working tree `1f81f3fc` plus the CiCd spine and both evidence records).

| # | Finding | Verdict | Route | Evidence |
|---|---------|---------|-------|----------|
| 14 | No test checks that declared builds (`buildProjects`) in a release receive the instant | medium | patch | Verification-gap layer, pre-verified. `test_platform_support.py` runs the release route at lines 416 and 419 without `clock` and never reads the flags; the two `assert_one_instant` tests have no `buildProjects`. |
| 15 | Inspection still treats `artifact.created` as optional although the release always emits it | maybe-false | rejected | The image would have to lose the label after `HexalithReleaseLabels`. Builds' `ContainerProvenance.targets` and Parties re-add both labels, and no target that drops it is known. It would be low only; a product target that removes the label would settle it. Design Notes keep the matrix's "when present". |
| 16 | Children may disagree on whether `artifact.created` is present | carried low | rejected | Carried row 3. |
| 17 | Builds `main` holds `7f085bad`'s `artifact.created` regression, and neither record calls it a release blocker | medium | patch | `git tag --contains 7f085bad` is empty, so nothing has shipped, but the next central release from `main` would ship it. |
| 18 | Fix base `7f085bad` is no longer current `main` | low | patch | `origin/main` is `74e6e4b5`, which adds only `Tools/g6-current-policy-2026-11-12.json` and does not overlap. |
| 19 | "Every SDK command" overstates: `dotnet sln list` and `dotnet tool restore`/`run` run without the instant | low | patch | These commands do not evaluate product properties, so the behavior is fine; the README Scope row, the spine and the `release.targets` comment overstate it. |
| 20 | Isolated preflight runs without the instant | carried false | rejected | Carried row 4. |
| 21 | Complete-mode test name promises "without rebuild or new instant" | low | rejected | The name states the matrix scenario and byte equality is the proof; renaming would orphan the citation in the committed `verification.json`. |
| 22 | `verification.json` keeps statements the fix superseded (decision, `plain_consumer`, `open`, SDK) | low | patch | The new record does not list what it supersedes. |
| 23 | Records name SDK 10.0.403, but local runs resolved 10.0.404 | low | patch | `latestPatch` plus 10.0.404 installed; hosted `builds-ci.yml` pins 10.0.404. `Microsoft.NET.Build.Containers.targets:152` is the same in 10.0.403 and 10.0.404. |
| 24 | Two lint runs record the same log digest; `unchanged_from_base` mixes formats | low | patch | The 106-byte zizmor token message does not depend on the tree. |
| 25 | No Actions run links | low | patch | Hosted CI run [44495264716](https://github.com/Hexalith/Hexalith.Builds/actions/runs/44495264716) passed for `7f085bad`. |
| 26 | `isolated-suite.sh` exists only as a digest | carried low | patch (moot: loopback) | Carried row 10; not patched again. |
| 27 | Diff omits the spec and the moved CiCd `references/Hexalith.Builds` gitlink | low | patch | The spec is the claims file by design. The gitlink moved because the submodule checkout is on the fix branch; staging it would be an unreviewed pin bump. |

## Design Notes

- **Name:** the prerequisite left it open. `ContainerProvenanceCreated` is Builds-owned, the legacy publisher passes it once per release, EventStore and Parties require it and Tenants imports Builds' targets, so story 21's mapping becomes identity.
- **Scope is labels:** this matches the legacy validator. The SDK's fractional config `created` stays as written, because rewriting it would change the child digests that `combine_archives` keeps unchanged.
- **Universal label:** the release already rebinds source/revision/version for every image, and both created labels follow suit. Modules without their own targets get a consistent value with no setup.
- **Both created labels:** turning off the SDK switch removes both labels, so the release rebinds both. This keeps the label set existing consumers already have, puts the one instant in every created label (prerequisite) and matches `Props/ContainerProvenance.targets`. Inspection still checks `artifact.created` when it is present, as the matrix says.

## Verification

**Commands (from `references/Hexalith.Builds`):**
- `run-with-temp python3 -m unittest discover -s Github/lib/tests -p 'test_release_*.py'` -- expected: all pass, including the real SDK container graph.
- `run-with-temp uv run --no-cache --locked --script --python 3.12 Tools/ci/run_python_tests.py` -- expected: full contract suite passes.
- `python Tools/ci/lint_workflows.py --export-path` -- expected: clean.
