---
title: 'Perimeter contract and library in Builds'
type: 'feature'
created: '2026-11-12'
status: 'done'
story_id: '4-1'
review_loop_iteration: 0
followup_review_recommended: false
baseline_revision: 811b04fa570bf575d1cb42f8b661ea6c05c25f61
implementation_repository: references/Hexalith.Builds
implementation_baseline_revision: 3238aa2742dd69ec75144a6f523fd1f86c3f3174
implementation_integration_revision: 3c2f5944aaa28dc7854a00a8a9df171aa810b0c7
implementation_source_revision: 9ebc31f606bc02f8a0ec2f1ec344127e2468c6b4
implementation_evidence_revision: 7917c50e21ec5bae15677c9ac3559623e432756e
published_builds_tag: v5.1.0
release_run_id: 43325614833
planning_only: false
context:
  - '{project-root}/_bmad-output/specs/spec-cicd/SPEC.md'
  - '{project-root}/_bmad-output/planning-artifacts/architecture/architecture-cicd-2026-11-07/ARCHITECTURE-SPINE.md'
warnings: [oversized]
deferred: ["RB9: verify older Git attribute-source capability (medium, unverified)"]
---

<intent-contract>

## Intent

**Problem:** Guard, restore and delivery need one versioned definition of ownership and one implementation of comparison and repair. Their future integrations must agree even when a module's owned files are malformed or absent from a sparse working tree.

**Approach:** Ship `hexalith.perimeter.v1`, its strict stdlib loader and one Git-backed comparison/application library in Builds, with executable fixtures for every AD-4 entry kind. After implementation and green CI, release from an interactive CiCd session and advance CiCd's `builds-version` to the verified published tag (CAP-4/8/15; AD-4/10/19).

## Boundaries & Constraints

**Always:** Use Python >=3.12 stdlib at runtime. Enumerate and read module paths from the selected HEAD tree or index, including expected rendered files from their Git snapshot. Write owned content only to the index and Git object database, using `hash-object -w --path`, `update-index --add --cacheinfo`, and `rm --cached --sparse`; never materialize repairs in the working tree. Keep ownership paths in the perimeter data. Preserve unrelated staged data, module-owned content, regular-file modes and submodule checkouts. Follow AD-4 repair-before-parsing, semantic partial comparisons and Git wildmatch rules. Only a later interactive CiCd session dispatches this release; no unattended continuation may dispatch it.

**Never:** Implement rendering, delivery, guard/restore jobs, release drift integration, or `check.py` in this story. Restore policies belong to their later callers. Builds has no delivered-ref perimeter of its own. Never restore `.github/actions/**`, initialize nested submodules, change AD-20 frozen runtime, edit package/catalog pins, add workflow-text assertions, change live release settings, publish a draft manually under the bootstrap exception, or move `builds-version` before acceptable publication. This resumed invocation implements and verifies the library, commits and pushes in Builds. Release dispatch is performed only by the parent interactive CiCd session after exact-source green CI and fresh prerequisites; implementation subagents and unattended continuations never dispatch. Adoption still requires acceptable publication.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
| --- | --- | --- | --- |
| Contract | Closed v1 document with any of the nine kinds | Schema and loader agree on validity; values remain explicit | Unknown/missing keys, unsafe paths, malformed UTF-8/JSON, duplicate serialized keys and non-JSON constants fail |
| Unsupported identity/kind | Unknown schema or entry kind | Fixed diagnostic, before any index mutation | `<file>: unsupported schema <value>. CI/CD is owned by Hexalith.CiCd.` or `<file>: unsupported perimeter entry kind <kind>` |
| Whole content | Missing/changed whole file or extra tracked whole-dir descendant; even malformed JSON | Compare blob bytes and expected modes without parsing module bytes; add/replace/delete to expected directory membership | Missing expected source blob is an error, never an empty render |
| Gitlink | Wrong/missing pointer, including an annotated expected tag | Resolve exact stable tag with `^{}` in the trusted Builds clone; stage peeled commit as mode `160000` | Missing/non-commit tag fails before apply |
| Partial ownership | Valid JSON, markers or Gitmodules with foreign content and CRLF | Semantic no-op leaves blob unchanged; repair only failed owned portion, preserving foreign data | Missing or unparseable partial file is drift; recreate only owned content |
| Absence | Forbidden globs, selected JSON keys/dependencies or matching hook lines | Remove only matches; preserve unrelated content; absent targets already pass | Malformed JSON needing absence repair becomes `{}`; unreadable line data becomes empty owned result |
| Git snapshots | HEAD, staged and dirty working-tree bytes disagree; sparse files missing | Selected snapshot determines result; working-tree bytes, untracked files and submodule checkout stay unchanged | Unmerged index or repair requiring edits outside selected ownership fails before mutation |
| Repeat/selection | Compliant index or a caller-selected subset of entries | Second apply makes no change; unselected entries and unrelated staged paths retain their identities | Invalid document/source/selector errors leave index unchanged |

</intent-contract>

## Code Map

All implementation paths below are relative to `references/Hexalith.Builds` unless prefixed `CiCd:`.

- `Github/lib/ci_config.py:20` (`SCHEMA_PATH`, `schema_identity`, `validate_config`, `_object`, `_constant`, `_read_json`) establishes own-checkout identity, strict JSON, closed objects, escaped diagnostics and isolated CLI. Reuse its approach without adding another perimeter validator or changing CI semantics.
- `Github/lib/tests/test_ci_config.py:30` demonstrates one corpus through `Draft202012Validator` and the stdlib loader; serialized-input/isolation controls start at line 184. `Github/lib/tests/fixtures/contract.json` is the existing CI corpus, preserved.
- `Github/lib/ci_pipeline.py:152` demonstrates NUL-safe index enumeration and Gitmodules reads. `Github/lib/release_state.py:160` (`Git.run`, `Git.blob`) is read-only precedent: it strips `GIT_INDEX_FILE` and lacks binary stdin, so do not reuse it unchanged for this writer. `Github/lib/release_draft.py:411` compares workflow trees with `ls-tree -z`.
- `Tools/ci/run_python_tests.py:20` (`commands`) already discovers `Github/lib/tests`; `.github/workflows/builds-ci.yml:171` runs the same locked suite on Python 3.12 and runner Python. `jsonschema==4.26.0` is already test-only and locked. No new CI job or runtime dependency is needed.
- `Tools/ci/check_public_api.py:124` includes schema files, fields, definitions and enums from committed Git objects. First perimeter-schema addition is minor; later new fields/kinds require perimeter v2 and a Builds major (AD-10).
- `.github/workflows/ci.yml:54`, `Github/lib/release_state.py:318` are deferred guard/drift seams. `Samples/Hexalith.Sample/README.md:20` and `Tools/ci/README.md:404` describe the sample placeholder perimeter: correct schema ownership wording, preserve the inactive enforcement seam for story 5-1.
- `.github/workflows/builds-release.yml:3` is dispatch-only, calls shared release with Builds rules/CI identity at lines 14-21, and owns artifact-only publication in `hexalith-release` at line 26. `Github/lib/release_version.py:29` determines the version; do not assume a next numeric tag.
- `CiCd:builds-version:1` is `v5.0.1` plus LF. All fourteen preceding story specs are done with completed execution lists. Story 3-7's latest acceptance supersedes earlier bootstrap blockers: immutable bot release `443097864` at `3c2f5944aaa28dc7854a00a8a9df171aa810b0c7`. Retained qualification draft `441591623` is unmarked for production selection; preserve it. Historical readiness is evidence, not a substitute for fresh checks.
- Starting Builds HEAD was `adfbf21896ef982ae9d1c3ee1db247e87bda22c0`; planning fast-forwarded three already-published product/catalog commits to `3c2f5944aaa28dc7854a00a8a9df171aa810b0c7`. Review this story's changes separately from that integration. Build the eventual review diff from both repository baselines; a superproject gitlink diff alone omits the implementation.

## Tasks & Acceptance

**Execution:**

- [x] `schemas/hexalith.perimeter.v1.json` -- add the draft-2020-12 public schema with the closed wire contract below, safe repository paths and all nine kinds -- establish the shared versioned interface.
- [x] `Github/lib/perimeter_config.py` -- implement one strict stdlib loader/validator, parsing bytes as well as files, deriving schema identity beside trusted code and retaining the fixed diagnostics -- let Git consumers validate without reading module working-tree files.
- [x] `Github/lib/perimeter.py` -- implement snapshot enumeration/blob reads, deterministic drift records, entry selection and index-only apply for all nine kinds -- provide the sole comparison/application engine for later guard, restore and delivery. Preflight the complete selected operation before mutation.
- [x] `Github/lib/tests/fixtures/perimeter-contract.json`, `Github/lib/tests/test_perimeter_config.py`, `Github/lib/tests/test_perimeter.py` -- add shared schema/loader valid-invalid fixtures and real temporary Git repositories covering the entire matrix, every kind and the Git-only boundaries below -- prove behavior through committed/index contents and unchanged working-tree bytes.
- [x] `.github/workflows/builds-ci.yml`, `Tools/ci/README.md`, `Samples/Hexalith.Sample/README.md` -- clarify the existing Python step name to cover both document contracts, document the API/fixtures and correct sample schema ownership -- run through existing discovery with no new job; leave story 5-1 enforcement inactive.
- [x] `docs/cicd-4-1-perimeter-contract-and-library-results.md` -- record validation, full source/integration revisions and hosted exact-source CI evidence; validate the actual releasable implementation commit with pinned commitlint, commit and push in Builds -- ship the additive contract as a `feat` minor, retaining existing API/frozen files.
- [x] `.github/workflows/builds-release.yml`, `docs/cicd-4-1-perimeter-contract-and-library-results.md` -- from a later interactive CiCd session, freshly verify release prerequisites, dispatch on main, correlate exact source/run/outcome/original artifact and verify acceptable publication -- complete the release operationally without changing the workflow or dispatching unattended. A non-bootstrap `ready` outcome waits for nightly publish-ready.
- [x] `CiCd:builds-version`, `CiCd:_bmad-output/specs/spec-cicd/stories/4-1-perimeter-contract-and-library-in-builds.md` -- after published immutable bot release/tag/source/ancestry verification, write the actual tag plus LF and record release evidence; stage with the pushed Builds gitlink -- unlock later render/delivery work without bumping any module now. Re-render and commit rendered changes together if such outputs exist by implementation time (AD-5).


**Acceptance Criteria:**

- Given one valid or invalid v1 fixture, when both existing hosted Python lanes run its JSON Schema and independent stdlib validation, then both agree with the recorded expectation; unknown identity/kind diagnostics match the fixed messages.
- Given real repositories exercising every matrix row and all nine kinds, when comparison and application run, then observed Git tree/index contents and drift records match the fixture expectations, repeat apply is unchanged, and working-tree bytes/untracked files/submodule checkouts are unchanged.
- Given foreign JSON keys/denies/allow lists, unrelated Gitmodules sections/keys, text outside a valid ownership block, unrelated hook lines and unrelated staged files, when an owned portion is repaired, then those foreign values and staged identities survive.
- Given dirty/sparse workspaces and conflicting working-tree attributes, when the selected Git snapshot is compared/applied, then results come from that snapshot and its attributes, with no filesystem-based glob/read/repair fallback.
- Given a pushed additive implementation commit, when `builds-ci.yml` executes, then retained shared Builds/sample/Windows, product catalog, quality/API and both Python lanes pass, with the new fixtures actually discovered and no workflow-text test added.
- Given successful exact-source Builds CI and freshly verified release prerequisites, when an interactive CiCd session dispatches Builds release on main and publication completes, then the published immutable bot-authored tag contains this schema/library and is an ancestor of Builds main; only then does CiCd `builds-version` name that exact tag. A `ready` draft alone does not satisfy this criterion.

## Spec Change Log

- 2026-11-12: The user resumed story 4-1 for implementation, commit and push in Builds, reiterating AD-4 Git/index boundaries and CAP-15 interactive dispatch. Removed the prior invocation-only planning stop; preserved all product constraints. Captured current superproject baseline `811b04fa570bf575d1cb42f8b661ea6c05c25f61` and implementation baseline `3238aa2742dd69ec75144a6f523fd1f86c3f3174`; the prior planning baseline/integration remain historical evidence below. The parent interactive session owns release operations.

## Review Triage Log

### 2026-11-12 — Review pass

- verdicts: 24 findings — high 3, medium 10, low 6, false 5, maybe-false 0
- findings:
  - `[medium]` `[patch]` B1: intent-to-add entries can report false compliance — disposable Git reproduction returned no drift for an expected empty file which `write-tree` omitted. Reject or correctly stage intent-to-add before comparison/application.
  - `[high]` `[patch]` B2: foreign JSON numeric precision is lost — reproduction changed `1.234567890123456789` to `1.2345678901234567`; `1e999` also prevented repair. Preserve numeric tokens/values without binary-float roundoff or non-JSON constants (shared root cause with E5).
  - `[false]` `[reject]` B3: duplicate matching Gitmodules sections lose their extra keys — the loss occurs in the removed duplicate, but AD-4 explicitly requires removing every other section with the same owned path. The retained matching section and unrelated sections keep their foreign records; retaining duplicate sections would contradict that specified removal.
  - `[high]` `[patch]` B4: successful clean filters can corrupt foreign content — a selected filter changed the indexed prefix from `foreign` to `CORRUPTED` while owned marker content passed. Validate the complete proposed blob's preservation after filtering, allowing the required CRLF semantic normalization.
  - `[low]` `[patch]` B5: schema-valid NUL marker bodies never converge — reproduced acceptance by the loader followed by candidate refusal. Honor the existing valid body through text handling and add a convergence regression (shared root cause with E4).
  - `[low]` `[patch]` B6: regex compiler failures escape controlled diagnostics — oversized repetition and nested groups raised `OverflowError` and `RecursionError`. Convert these compiler failures to the existing ConfigError path (shared root cause with E1).
  - `[medium]` `[patch]` B7: partial repair rewrites foreign CRLF ranges — with `-text` attributes, repairing a block and deleting a hook line changed retained CRLF bytes to LF. Normalize only comparison/matching semantics and preserve unedited input ranges before Git's required conversion.
  - `[false]` `[reject]` B8: Git info/global attributes are not disabled — AD-4 expressly requires `hash-object --path` so the module's attributes apply, and pins snapshot `.gitattributes` to prevent dirty working-tree influence. Trusted Git metadata/configuration is not excluded by that rule. The demonstrated owned-content transformation already fails atomically; no additional isolation promise is introduced.
  - `[medium]` `[patch]` B9: expected symlink blobs incorrectly receive regular-file filtering — reproduction with a mode-120000 expected blob and uppercase clean filter failed repair. Preserve the raw symlink target bytes while retaining path-based conversion for regular files.
  - `[low]` `[patch]` B10: the ECMAScript parity test omits Unicode mode and astral fixtures — `x🦄` passes the loader and JavaScript `u` mode but fails the test's plain RegExp mode. Use the Unicode behavior recommended by JSON Schema 2020-12 section 6.4 and cover non-BMP data; the published schema need not change for this issue.
  - `[medium]` `[patch]` B11: descending bracket ranges differ from Git — Git matched `xb`, `xz`, and `xa` for `x[b-a]`, `x[z-a]`, and `x[a--]` respectively while the library matched none. Preserve Git's endpoint semantics with oracle controls (shared root cause with E3).
  - `[medium]` `[patch]` B12: an existing default-named Gitmodules section without path is incorrectly treated as a different-path collision — reproduced with url/custom only. Complete the missing owned path and retain foreign records; keep actual different-path collisions atomic.
  - `[low]` `[patch]` E1: oversized/deep line regexes escape validation — same verified compiler failures as B6; use the same controlled-exception correction and CLI regression.
  - `[medium]` `[patch]` E2: EOF continuations consume appended Gitmodules records — a valid foreign final value ending in backslash caused the appended owned section to become value data and repair failed. Terminate the existing logical record safely while preserving its parsed value, both for new sections and appended owned fields.
  - `[medium]` `[patch]` E3: descending bracket ranges are missed — same Git-oracle reproduction and correction as B11.
  - `[low]` `[patch]` E4: valid NUL marker bodies cannot apply — same accepted-document/failed-apply reproduction and correction as B5.
  - `[high]` `[patch]` E5: unrelated JSON numbers change during repair — same precision-loss reproduction and correction as B2.
  - `[medium]` `[patch]` V1: extra whole-directory member removal lacks an independent oracle — the pre-verified mutation disabled descendant removal while all 31 engine tests passed. Add explicit unexpected-drift and final index-membership assertions.
  - `[medium]` `[patch]` V2: the concurrent-stage identity rejection lacks coverage — the pre-verified mutation removed the guard without failing the suite and overwrote new staging. Add a deterministic real-Git interleaving assertion that checks preservation of the newly staged index.
  - `[false]` `[reject]` I1: the AD-4 observable surface aligns — the auditor expressly confirms real Git snapshots/indexes and untouched working trees; there is no divergent behavior to fix.
  - `[false]` `[reject]` I2: tests do not audit every filesystem read — inspection shows filesystem content reads are limited to trusted schema/code and selected index metadata; module paths/blobs come from Git. Those permitted reads do not refute the module-content boundary.
  - `[false]` `[reject]` I3: production guard/restore/delivery integration is absent — story 4-1's inherited intent explicitly excludes those later integrations. The fixture/library surface is the intended scope and the sample seam remains inactive.
  - `[low]` `[patch]` I4: operational validation evidence is stale in the results companion — both local interpreter runs, API results and remote identities are independently available. Refresh the final results companion with actual final-source hosted evidence after verification.
  - `[medium]` `[patch]` I5: publication and builds-version adoption are still outstanding — these are explicitly authorized parent interactive operations in the captured intent, not an unresolved intent choice. Complete exact-source CI, fresh preflight, single dispatch and acceptable-publication verification before adoption; a ready draft remains insufficient.

The 24 individual verdicts above precede grouping. Shared causes are B2/E5, B5/E4, B6/E1 and B11/E3. The 15 remaining patch entries have no new public surface and correct only reproduced states or demonstrated verification gaps; no intent/spec loopback or deferred item is required. Runtime corrections were applied by the re-engaged implementation agent, and both parent focused lanes passed all 50 tests. The B1 correction additionally compares full raw records so a stale alternate index cannot hide intent-to-add behind equal changed-path names. Final operational/evidence corrections remain with the parent interactive session.


### 2026-11-12 — Review patch verification

- verdicts: 1 additional finding — high 1, medium 0, low 0, false 0, maybe-false 0
- findings:
  - `[high]` `[patch]` B13: a bracket range consuming the opening `[` of a POSIX class could overmatch and delete unrelated paths — differential comparison reproduced four mismatched class bodies. The scanner now consumes literal range tokens consistently with its body parser. A Git-oracle regression checks matching names ending in `]`, preservation of unrelated paths and repeated apply.

Two independent validators then reproduced no remaining defect in the repaired areas. Final byte wildmatch agrees with Git for 1,419 patterns across 197 tracked filenames; composed JSON orders preserve precise decimals, large exponents, negative zero and 5,000/6,000-digit integers; foreign-changing filters fail atomically for every partial kind; Gitmodules continuations preserve parsed values; and explicit/inherited alternate indexes reject stale intent-to-add entries without mutation. These checks also settle the specific high-risk numeric/filter/bracket paths after repair.

### 2026-11-12 — Resumed review

All three review layers completed before triage. The 14 findings below are
individual verdicts, before grouping: high 2, medium 6, low 3, false 2,
maybe-false 1.

- `[medium]` `[patch]` RB1: `splitlines()` treats Unicode separators, vertical tabs and bare CR as shell record boundaries. A hook reproduction retained part of a physical line containing commitlint. Split only at LF and normalize CRLF for matching.
- `[high]` `[patch]` RB2: the same splitting changes valid foreign Gitmodules values; `custom=keep\u2028url=foreign` lost its suffix during an owned URL repair. Preserve complete physical records and verify their parsed values with Git.
- `[medium]` `[patch]` RB3: Git accepts CR before a section header, but the scanner omitted that section and falsely accepted a duplicate appended repair. Recognize Git's accepted CR header whitespace and assert the staged owned URL/path independently.
- `[medium]` `[patch]` RB4: repeated stars compiled into a backtracking regex stall on a 200-byte filename. Match finite sets of byte positions instead; a timed subprocess exercises the demonstrated pattern.
- `[low]` `[patch]` RB5: recursive directory matching raises RecursionError for a Git path with 995 components. The direct iterative position-set correction also covers paths that are never materialized.
- `[low]` `[patch]` RB6: valid JSON near the interpreter recursion limit can parse but fail during unnecessary serialization of an already-compliant superset. Independent unpatched Python 3.12 reproduction uses 994 nested arrays with a string leaf; the reviewer reproduced depth 996 on Python 3.14. Return the original compliant bytes and convert repair serialization overflow to PerimeterError, preserving the index.
- `[low]` `[patch]` RB7: a 5,000-digit array pointer raises an uncontrolled integer-conversion ValueError. Compare its length with the array bound before conversion and retain the existing controlled pointer error.
- `[high]` `[patch]` RB8: malformed bracket expressions can match and remove unrelated literal paths. `x[a][]` matched `xa[]`; Git's ignore/wildmatch oracle matches neither that name nor the literal pattern. Reject an unterminated class and use Git check-ignore for these cases because glob pathspecs can short-circuit exact literals.
- `[maybe-false]` `[defer]` RB9: older Git may ignore GIT_ATTR_SOURCE. No supported older binary was available to establish the exact failing version/behavior; defer the medium unverified compatibility claim with a required cross-version reproduction. Current hosted/local Git honors the attribute source and passes dirty-attribute controls.
- `[false]` `[reject]` RB10: the portability claim says the documentation specifies Python without a platform restriction. Tools/ci/README.md explicitly starts with Linux x86_64; the Windows job invokes no Python. No Windows execution promise is established by this change.
- `[medium]` `[patch]` RE1: a leading UTF-8 BOM similarly hides the first valid Gitmodules section. Strip only that parsing prefix and preserve it in repaired bytes; verify a single expected owned path/URL through Git.
- `[false]` `[reject]` RE2: carried B3 — later duplicate sections for the owned path are expressly removed by AD-4. Losing records in those removed sections is the specified duplicate-removal behavior; retained sections and unrelated sections preserve foreign records.
- `[medium]` `[patch]` RV1: pre-verified mutation retained only the first required JSON superset value while all engine tests passed. Assert every manifest-required deny and independently exercise a partially present three-value requirement.
- `[medium]` `[patch]` RV2: pre-verified mutation ignored URL-only Gitmodules drift while all engine tests passed. Assert the initial drift record and exact staged URL using Git's own parser.

RB1/RB2 share the physical-line splitting root cause. RB3/RE1 share incomplete
Git header enumeration. All other surviving patch findings remain separate.
No new public field, schema identity, ownership path, workflow assertion or
release policy is introduced. The prior implementation agent is unavailable in
this resumed session, so the parent applied the smallest runtime/test patches.

Follow-up `[medium]` `[patch]` RB11: a 519-pattern/591-path differential check found three malformed POSIX openers scanned past an earlier closing bracket. For `x[[:]:]`, Git matches `x[:]` and `x::]`; the engine missed both. Stop POSIX scanning at the first closing bracket, require the immediately preceding colon, and assert both oracle matches and final index membership. This is distinct from RB8's unterminated-class overmatch and has its own regression.

Final resumed matching validation reports zero mismatches for all 519 patterns across 591 paths. Both final locked focused environments pass 58 tests, including all 129 schema/loader cases. Authenticated lint retains exactly 10 frozen findings and no new finding; committed-object public API validation passes against v5.0.1 with 2,579 entries and no removal. Exact message `fix(cicd): preserve Git perimeter matching semantics` passed pinned commitlint 21.2.4 with zero problems/warnings. Builds commit `9ebc31f606bc02f8a0ec2f1ec344127e2468c6b4` is pushed to origin/main, with no ruleset bypass warning. Local full suites and exact-source hosted CI run 43322385361 remain in progress at this record; no release dispatch or builds-version change has occurred.

Local retained-suite terminal evidence: the initial two full processes passed 13/14 groups, having imported the bracket matcher before its final correction. Targeted reruns of the sole affected library group on committed `9ebc31f606bc02f8a0ec2f1ec344127e2468c6b4` passed all 354 tests on both interpreters. The other 13 groups passed unchanged; combined coverage includes every retained group. This does not describe either initial full command as successful. Exact-source hosted CI executes the complete suites independently. Details: [retained Python groups](../evidence/4-1/verification-9ebc31f606bc/retained-python-groups.json).

Concurrent CiCd advance observed during verification: another workspace operation created merge `49834a984056db7f1439230bb653a50e5e6381b5` and submodule synchronization `9c3ff38a0580c68b325271c02c8aaab9b7382936`. The difference from original baseline `811b04fa570bf575d1cb42f8b661ea6c05c25f61` changes only seven root gitlinks, including the already-pushed Builds source. This invocation preserves those commits, records current head separately, and has not committed or pushed CiCd. The accepted `builds-version` remains v5.0.1.

Hosted final-source CI [43322385361](https://github.com/Hexalith/Hexalith.Builds/actions/runs/43322385361) passed all seven jobs at `9ebc31f606bc02f8a0ec2f1ec344127e2468c6b4`. Both hosted Python logs independently confirm every new perimeter control and 14/14 retained groups. [Fresh preflight](../evidence/4-1/preflight-20261112T230254Z/preflight.md) passed all 39 checks at 23:04 UTC. Exactly one interactive dispatch produced [release run 43325614833](https://github.com/Hexalith/Hexalith.Builds/actions/runs/43325614833), attempt 1, at that same full source. Original dispatch/request correlation is retained in the adjacent release evidence directory. The run is in progress; no publication or new version acceptance is claimed yet.

## Design Notes

### Initial v1 wire contract

Root keys are exactly `schema` (constant `hexalith.perimeter.v1`) and `entries` (array). Each entry requires `kind` plus exactly the fields below; all keys are explicit, without reader defaults. The schema `$id` is `https://hexalith.com/schemas/hexalith.perimeter.v1.json`.

| Kind | Other required fields | Meaning |
| --- | --- | --- |
| `whole` | `path` | Expected blob/mode at the same relative path beneath caller-supplied rendered root |
| `whole-dir` | `path` | Complete tracked descendant membership/blobs/modes beneath that directory; directory path has no trailing slash |
| `gitlink` | `path`, `buildsTag` | Exact stable tag resolved in caller-supplied trusted Builds repository |
| `gitmodules-section` | `path`, `submodulePath`, `url` | File path and section identity by submodule path; expected URL inline |
| `json-superset` | `path`, `pointer`, `values` | RFC 6901 pointer to array of required unique strings; array may contain additional module-owned strings |
| `marker-block` | `path`, `text` | Inline block body, enclosed in the fixed AD-4 begin/end markers |
| `absent-glob` | `pattern` | Remove tracked paths matching repository-root-relative Git wildmatch |
| `absent-json` | `path`, `selectors` | Nonempty arrays of JSON key components; component `*` wildcards select property names, including names containing `/` |
| `absent-line` | `path`, `pattern` | Python regex matched against individual normalized lines; remove matching complete lines |

The loader closes/type-checks nested objects, rejects unsafe paths (absolute/drive, backslashes, empty/dot/traversal segments, controls, `${{`), validates pointer escapes, stable tags and compilable regexes. Wildcards are allowed only in pattern/selector fields. Cross-entry conflicting ownership and file/directory overlaps must fail before mutation; disjoint partial entries on one file may be composed. Empty `entries` is valid for a zero-owned-path fixture; `{}` is invalid.

The library API takes trusted Git repository/snapshot handles, rendered-root prefix, Builds tag-resolution repository and an optional selected entry set. It returns deterministic path/kind/reason drift records. Compare accepts HEAD or index; apply derives changes from the current selected index, optionally through a caller-selected `GIT_INDEX_FILE`. Expected data may use a pinned Git tree. No API clones, commits, pushes, dispatches or embeds an ownership path list. This permits future restore to exclude workflows and lockstep entries using caller policy.

Git uses binary stdin and NUL-separated literal paths, with index stage/mode validation. Preserve regular modes; create missing/malformed partial text files as `100644`. Whole entries restore expected modes, including replacing an owned symlink/gitlink; non-regular partial targets are malformed and repaired to owned content without following links. Reject file/directory conflicts if repair would remove paths outside selected ownership. Resolve all expected sources/tags and reject unmerged indexes before writes. Pin attribute resolution to the selected index tree (for example `write-tree` plus `GIT_ATTR_SOURCE`) while hashing with `--path`, so dirty `.gitattributes` cannot affect repairs. Deletions may need `--force` on `rm --cached --sparse` to avoid working-tree freshness checks on staged drift; use exact enumerated paths only. Preserve the caller's explicitly selected index rather than stripping all `GIT_*` indiscriminately.

Git wildmatch fixtures cover `*`, `?`, bracket classes and zero/multiple-directory `**/`; ordinary `fnmatch` or default Git pathspec globbing is insufficient. Test actual AD-4 patterns: root config globs, `**/Directory.Build.rsp` at root and depth, and `**/bmad-testarch-ci/**`. Use Git glob-pathspec matching as an oracle where compatible. Whole blobs compare byte-for-byte; CRLF normalization applies to partial semantics only. Do not rewrite a passing partial entry.

For Gitmodules, preserve the existing matching section name (first in file order if duplicates), default to `submodulePath` if missing, own `path`/`url`, remove `branch`/`update` and duplicate sections with that path, and retain other keys/sections. If that default name already belongs to a different path, fail preflight rather than overwrite unrelated state. Parse Git syntax rather than assuming INI equivalence. For JSON superset, union missing required strings without deleting/reordering extras or touching allow lists. Markers are exactly `<!-- hexalith-cicd:begin -->` and `<!-- hexalith-cicd:end -->`. Valid marked text replaces only one well-formed block; no markers appends it preserving existing text; unbalanced/repeated markers are malformed and repair to the owned block only. Missing/malformed partial JSON or Gitmodules similarly repairs to only owned state. Absence-only malformed JSON becomes `{}`; valid unrelated content is preserved. Hook matching removes only matching full lines.

Fixture manifests, not library constants, describe the AD-4 perimeter: workflows whole-dir; CI/dependabot whole; Builds gitlink/section; permissions.deny; three instruction blocks; forbidden config/response/skill globs; package.json root `release`/`commitlint` and `semantic-release`, `@semantic-release/*`, `@commitlint/*` pins in dependencies/devDependencies/optionalDependencies/peerDependencies; commitlint hook lines. Include extra workflow files, malformed owned whole JSON, CRLF no-ops, missing partials, duplicate sections/markers, literal special-character filenames, annotated tags, sparse/outside-cone deletions, staged and dirty attribute conflicts, caller-selected indexes, type conflicts and preflight failure without index mutation.

### Continuity and publication

The initial schema addition is minor, with a releasable `feat` implementation commit. Planning uses `docs` and does not create a release. The actual tag comes from shared version calculation, never a guessed number. Fresh preflight covers true/false switch, main-only environment/publish identity, immutable releases, retention/rulesets, current drafts and exact-source green CI. Follow the existing shared original-artifact protocol; retain qualification resources. Read-only auth failure leaves a prerequisite unverified and must report the intended profile, command and required access. Interactive dispatch uses the configured CiCd-agent profile, never an unattended maintainer credential. If execution is resumed unattended, complete code/verification and leave dispatch for the interactive CiCd session; the story remains incomplete until release/adoption acceptance passes.

Primary Git references for implementation: [wildmatch rules](https://git-scm.com/docs/gitignore), [attribute source](https://git-scm.com/docs/git#Documentation/git.txt---attr-sourcetree-ish), [hash-object path filters](https://git-scm.com/docs/git-hash-object), [index cacheinfo](https://git-scm.com/docs/git-update-index), and [cached/sparse deletion](https://git-scm.com/docs/git-rm). These support the Git mechanisms; AD-4 remains the ownership contract.

## Verification

Implementation commands run from Builds with documented Node/.NET/PowerShell and integrity-checked tool prerequisites:

- `python3 -m unittest discover -s Github/lib/tests -p 'test_perimeter*.py' -v` -- focused behavior/parity suite; use the locked runner environment if test-only jsonschema is unavailable.
- `uv run --no-cache --locked --script --python 3.12 Tools/ci/run_python_tests.py` -- full retained suite, including all new fixtures; repeat once with the captured runner interpreter.
- `python3 Tools/ci/lint_workflows.py` -- pinned actionlint and authenticated online zizmor audits pass.
- `uv run --no-cache --locked --script --python 3.12 Tools/ci/check_public_api.py` -- run after committing; additive committed-object API passes against current reachable release.
- `gh workflow run builds-release.yml --repo Hexalith/Hexalith.Builds --ref main` -- later interactive CiCd session only, after exact-source CI and fresh prerequisites. Verify actual run/outcome/artifact/release/tag; do not execute during planning.

For this implementation invocation, run the implementation checks above and validate exact commit messages with Builds' pinned commitlint 21.2.4. Commit and push implementation and evidence in Builds. Stage this canonical story and the pushed Builds pointer in CiCd. The parent interactive CiCd session performs release dispatch and verifies publication before changing builds-version. No CiCd commit or push is requested.

## Auto Run Result

Status: done

Story 4-1 is implemented, reviewed, verified, released and adopted. The additive
contract and sole Git/index library support all nine AD-4 kinds; 129 schema
cases, both 58-test focused lanes, both 354-test library reruns and final-source
hosted CI pass. CI run 43322385361 passed every one of its seven jobs and both
complete 14-group Python lanes. All review findings have individual verdicts;
RB9 remains one explicitly unverified medium older-Git capability follow-up in
the deferred-work ledger. No intent/spec loopback was needed.

The 39-check fresh preflight preceded exactly one interactive release dispatch.
Run 43325614833, attempt 1, produced authenticated outcome `published` from
`9ebc31f606bc02f8a0ec2f1ec344127e2468c6b4`. Published immutable bot release
443617691 / `v5.1.0` peels to that full source. Original release artifact
13992553006 has verified API/trailer/download digest
`sha256:b582f9ea801ca3970a88c87eff98068bbb3eb9250a98615ea07195aefa7d3f6a`;
outcome artifact 13992897976 has verified ZIP digest
`sha256:70278e0eccb1e2f247dd1d3103503110e0c961049f0ba55bf57879f89ffb7e3c`.
The original payload contains two Builds CLI packages and no containers.
Every prior release/tag and the qualification draft/artifact are independently
verified unchanged. No manual publication, redispatch, rebuild or settings
change occurred.

Only after acceptance did this invocation write `v5.1.0` plus LF to
`builds-version`. No rendered outputs exist yet. Final results and completion
evidence are committed and pushed in Builds at
`7917c50e21ec5bae15677c9ac3559623e432756e`; that commit changes only documentation/evidence,
retains the published runtime blobs and descends from the release tag.
Pinned commitlint 21.2.4 validated both exact commit messages with zero problems
or warnings; both pushes completed without a bypass warning. The canonical
story, updated pin, pushed Builds gitlink, deferred record and sanitized
verification/preflight/release evidence are staged in CiCd. This invocation
created no CiCd commit or push; the independently observed concurrent
submodule synchronization remains preserved.

Evidence: [verification](../evidence/4-1/verification-9ebc31f606bc/ci-verification.json),
[fresh preflight](../evidence/4-1/preflight-20261112T230254Z/preflight.md),
[publication and adoption](../evidence/4-1/release-20261112T230411Z/publication.md).

### Historical planning result


Status: ready-for-dev

Planning completed on 2026-11-12 with three read-only investigation subagents. The READY FOR DEVELOPMENT gate passed after rereading the rendered workflow and this story from disk: actionable paths, dependency order, Given/When/Then criteria, observable library/CI/release surfaces, complete v1 decisions and no unresolved intent gap. All eight implementation/release tasks remain unchecked. `oversized` records the contract detail needed for nine entry kinds.

Planning validation passed for both documents' frontmatter, canonical Git baselines, local links, template completeness, task/acceptance structure and whitespace. No runtime code, workflows, schema, version pin or live release state was changed; no runtime test suite or release dispatch ran. The Builds planning companion is `docs/cicd-4-1-perimeter-contract-and-library-plan.md`.

Builds planning commit: `3238aa2742dd69ec75144a6f523fd1f86c3f3174`, committed and pushed to `origin/main` using `/home/administrator/.config/gh-cicd-agent` (token override variables absent). Only the 175-line planning companion changed relative to the integrated upstream revision. Pinned `@commitlint/cli@21.2.4` validated the exact message `docs(cicd): plan the shared perimeter contract and library` via `node_modules/.bin/commitlint --edit /tmp/cicd-story-4-1-commit-message.txt --verbose`: exit 0, `found 0 problems, 0 warnings`. Fetch/divergence checks and staged whitespace checks passed; push completed without a ruleset bypass warning. The canonical story and pushed Builds gitlink are staged in CiCd; no CiCd commit/push. Requested halt after planning; release and `builds-version` adoption await implementation and interactive dispatch.
