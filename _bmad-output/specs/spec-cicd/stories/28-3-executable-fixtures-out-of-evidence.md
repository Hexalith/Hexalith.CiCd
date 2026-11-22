---
title: 'Executable fixtures out of evidence'
type: 'refactor'
created: '2026-11-22'
status: 'done'
baseline_revision: '539299f4800073aeaee52e98a0e596144ef34fe1'
review_loop_iteration: 0
followup_review_recommended: false
context: []
warnings: [oversized]
deferred:
  - summary: >-
      The relocated EventStore verifier suite is not discovered by the CiCd tool-suite gate.
    evidence: |-
      check_global.run_tool_tests globs only tools/tests/test_*.py, so
      tools/qualification/pre-adoption/eventstore/test_pre_adoption_verify.py
      (17 tests) runs only when invoked by hand. Pre-existing: the suite was
      equally undiscovered under evidence/20. It needs jsonschema and Builds
      release fdda17c0a4538b0f7c99f813c20ca24b49006530 objects at
      references/Hexalith.Builds, so gate wiring needs a prerequisite decision.
    location: >-
      tools/check_global.py:401
    severity: medium
  - summary: >-
      Live in-progress procedures still name executables under evidence, which AGENTS.md now forbids without exception.
    evidence: |-
      spec-23-migrate-tenants.md (in-progress) names evidence/23/read-preflight.py
      for the next read-only AD-21 refresh and evidence/23/qualify-eventstore-snapshot-candidate.py;
      eventstore-release-readiness-20261117 READMEs invoke evidence-resident verify
      and audit scripts. Pre-existing: the removed AGENTS.md sentence exempted only
      the runbook-named pre-adoption runners for stories 17, 18, 20 and 21, which
      this story relocated. Resolution needs AGENTS.md wording or relocating story
      23 tooling, both outside this story.
    location: >-
      _bmad-output/implementation-artifacts/spec-23-migrate-tenants.md:64
    severity: medium
  - summary: >-
      The Parties publication runner's exact-input checks are bare asserts that python3 -O removes.
    evidence: |-
      tools/qualification/pre-adoption/parties/qualify-push.py checks HEAD and
      origin, patch identity, dependency pins, untracked source bytes and modes and
      the expected tree with assert; under -O they vanish and the record reports
      result pass. Pre-existing and unchanged by the path-only relocation, which
      forbids logic changes; other repository procedures use run-with-temp
      python3 -O -B, so the pattern can be copied.
    location: >-
      tools/qualification/pre-adoption/parties/qualify-push.py:32
    severity: medium
---

<intent-contract>

## Intent

**Problem:** A tool suite imports a runner from evidence, and approved preparation procedures execute evidence scripts and read historical fixtures. Treating these paths as prose before migrating their consumers could skip validation of executable inputs.

**Approach:** Move active runners and their required fixtures to `tools/qualification/`, update live consumers and output paths, and enforce the evidence/registry dependency boundary with tool tests. Qualify the relocated consumers from a clean checkout and retain compact identities and results.

## Boundaries & Constraints

**Always:** Follow the approved 2026-11-18 proposal §4.1 (28-3) and added 2026-11-19 acceptance. Keep runner logic unchanged except paths, including exact-source checks, product checks, failures, released policy and authorization. Put disposable work and default raw output beneath `run-with-temp`'s `TMPDIR`. Preserve immutable proof inputs; record old/new runner blobs and explain path changes. Update docs, story 20's invoke note, and AGENTS Evidence's transitional sentence.

**Never:** Expand migration/publication authority, push modules, edit their owned portions, weaken audits/tests, delete unrelated historical evidence, rewrite history, or implement other 28-series stories.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|---|---|---|---|
| Live consumer | Relocated runner, frozen fixture, disposable source | Same checks and results at new paths; raw output in scratch | Existing refusal remains visible |
| Evidence dependency | Tracked executable/shared input references evidence | Tool test fails with path/line | Prose and identity-bound historical provenance are distinguished |
| Registry dependency | Suite reads repository-root setup/rendered through aliases or helpers | Tool test fails | Disposable fixture registries remain valid |

</intent-contract>

## Code Map

- `tools/tests/test_g6_host_ports.py:12` imports `evidence/18/qualify-owning-g6.py`; move runner to `tools/qualification/qualify-owning-g6.py` and selectors to its fixtures. `local-package-build.py:133` also invokes it.
- `evidence/17/verify-product-candidate.py`, `verify-final-candidate.py`: Folders runners; resolve CiCd/common Git paths, separate fixture reads from scratch outputs. Inputs: registration configuration and attempt-1/2/3 receipts.
- `evidence/18/local-package-build.py`: Projects runner, root via `__file__.parents[5]`; invokes G-6 with Projects runtime root.
- `evidence/20/pre-adoption-verify.py`, `test_pre_adoption_verify.py`: EventStore runner/root and sibling planned configuration fixture. Required report path already explicit; preserve that contract.
- `evidence/21/publication/qualify-push.py`: Parties runner; state, accepted receipt, patch, normalization and dynamic unit receipt are active inputs; messages/report currently written beside code.
- `_bmad-output/implementation-artifacts/spec-fix-package-owner-loading.md` (draft) has a live reuse note; `_bmad-output/implementation-artifacts/spec-fix-projects-publication-gates.md` (in-progress) has a frozen historical runner reference. Update the former and append a relocation note outside frozen intent in the latter.
- `docs/pre-adoption-publication.md`, `stories.yaml` entry 20, `ARCHITECTURE-SPINE.md` approved substitute reference, `AGENTS.md`: live procedure consumers.
- `tools/check_global.py:401`: auto-discovers `tools/tests/test_*.py`; new stdlib suite needs no registration.
- Seven shared provenance inputs (`docs/contracts-prerequisites/{approval,eventstore-tests,mcp,projects-source,projects-tests}.json`, policy patch, Works resync JSON) contain historical path strings, not CiCd path reads. Keep exact bytes and bind narrowly recorded exceptions to their identities; do not classify their directories as prose.

## Tasks & Acceptance

**Execution:**
- [x] `tools/qualification/` — relocate the seven named runner/test files and live fixtures; change paths only, direct output into scratch, and preserve historical source identities.
- [x] `tools/tests/test_g6_host_ports.py`, `docs/pre-adoption-publication.md`, story 20 in `stories.yaml`, architecture substitute reference, `AGENTS.md` — update consumers and remove the transitional exception.
- [x] `tools/tests/test_repository_inputs.py` and supporting qualification tests — enforce tracked evidence and real-root registry dependency boundaries, with meaningful negative controls and scratch-fixture positives.
- [x] Story record — record old/new blob IDs, fixture inventory, exact clean-checkout source/tree, invocations, log digests and honest execution limits.

**Acceptance Criteria:**
- Given owning G-6 and its consumers, when the affected suite and Projects caller resolve the runner, then both use `tools/qualification/qualify-owning-g6.py` and selectors outside evidence.
- Given the approved Folders, Projects, EventStore and Parties runners, when relocated under `tools/qualification/pre-adoption/<module>/`, then their live fixtures resolve there, default output is outside evidence, and their checks remain unchanged apart from paths.
- Given live procedure references, when read, then the runbook and story 20 point at new paths, and AGENTS no longer permits runners in evidence.
- Given a tracked non-prose evidence dependency or a suite reading repository-root `setup/` or `rendered/`, when tool tests run, then they fail; disposable fixture reads and documented identity-bound provenance remain valid.
- Given a clean candidate checkout and disposable inputs, when affected tests and every active qualification entry point execute, then relocated paths are exercised and exact source identities, results and digests are recorded without claiming product/publication acceptance from simulated dependencies.

## Spec Change Log

## Review Triage Log

### 2026-11-22 — Review pass

- verdicts: 23 findings — high 0, medium 20, low 0, false 3, maybe-false 0
- findings:
  - `B1` `[medium]` `[patch]` Reconstructed evidence path in an ordinary tool bypasses the literal scan — Disposable tools/candidate.py with concatenated marker and read_text returned no findings; extend resolved evidence-read analysis beyond suites.
  - `B2` `[medium]` `[patch]` Relative registry reads are not rooted at suite cwd — Disposable open(setup/Fixture.yml) returned no finding; normalize known relative reads against suite checkout.
  - `B3` `[medium]` `[patch]` Multi-part Path constructors discard components — Disposable Path(ROOT, setup, Fixture.yml) returned no finding; fold all path components.
  - `B4` `[medium]` `[patch]` Standard-library import aliases erase path/read identities — Disposable pathlib.Path and io.open aliases returned no finding; retain canonical callable aliases.
  - `B5` `[medium]` `[patch]` Branch-assigned path bindings are discarded — Disposable conditional registry assignment followed by read returned no finding; merge branch bindings.
  - `B6` `[medium]` `[patch]` Test setup state is lost between methods — Disposable setUp assigning self.registry followed by test read returned no finding; propagate fixture state.
  - `B7` `[medium]` `[patch]` Tuple unpacking erases path values — Disposable registry, other assignment returned no finding; preserve unpacked path association.
  - `B8` `[medium]` `[patch]` Constant-key dictionary path lookup is ignored — Disposable registries[input] read returned no finding; propagate keyed path values.
  - `B9` `[medium]` `[patch]` Comprehension read ignores generator binding — Disposable registry-path comprehension returned no finding; bind generators before examining body.
  - `B10` `[medium]` `[patch]` Glob pattern hides a root registry traversal — Disposable ROOT.glob(setup/*.yml) returned no finding; incorporate pattern path into reads.
  - `E1` `[medium]` `[patch]` Relative registry reads bypass the guard — Same verified defect as B2; share its normalization fix.
  - `E2` `[medium]` `[patch]` Branch alias loses root identity after conditional — Same verified defect as B5; share its binding merge fix.
  - `E3` `[medium]` `[patch]` Multi-part pathlib construction loses registry suffix — Same verified defect as B3; share its constructor-fold fix.
  - `E4` `[medium]` `[patch]` Aliased pathlib constructor bypasses path analysis — Same verified defect as B4; share its canonical alias fix.
  - `E5` `[medium]` `[patch]` Positional-only helper parameter is never bound — Disposable root positional-only helper returned no finding; bind posonlyargs with ordinary parameters.
  - `E6` `[medium]` `[patch]` Reconstructed evidence read outside suites escapes flow scan — Same verified defect as B1; share its executable evidence-flow scan.
  - `V1` `[medium]` `[patch]` Parties successful message outputs lack behavioral verification — Pre-verified reviewer mutation from OUTPUT to HERE passed existing integration test; add controlled success case asserting both message contents and scratch paths.
  - `V2` `[medium]` `[patch]` setUp self.root is lost before test methods — Pre-verified duplicate of B6; share fixture-state propagation fix.
  - `V3` `[medium]` `[patch]` Conditional alias is lost before later registry read — Pre-verified duplicate of B5; share branch binding fix.
  - `I1` `[false]` `[reject]` Literal strings versus semantic evidence dependencies — The eight exact identity-bound payloads contain inert receipt or embedded module-source names, never followed CiCd evidence inputs; they remain shared validation inputs. Changing or copying them fails. This reports an intentional documented data distinction, not a skipped executable dependency.
  - `I2` `[false]` `[reject]` Controlled exercise versus fresh product qualification — Approved relocation acceptance asks to exercise consumers on disposable inputs; the real bodies and fixture/output reads execute, and the record explicitly excludes real product/publication acceptance. No requirement to rerun historical product qualification or authenticated publication is introduced.
  - `I3` `[medium]` `[patch]` Whole-entry-point Parties success coverage is missing — Parties success-path output coverage is the same demonstrated gap as V1; add that case. Folders failed/blocked results are preserved existing behavior, not relocation defects.
  - `I4` `[false]` `[reject]` Clean source identity versus controlled operational environment — Both snapshots were actual clean detached checkouts; generated disposable runner inputs and controlled tools are separately disclosed. There is no claim that source identity proves real product/tool outcomes.

The 20 patch findings form 12 implementation corrections (duplicate claims share
the same fix). All are demonstrated path-flow or output-coverage omissions;
existing required behavior and public runner interfaces remain unchanged.
All 12 corrections were applied and their covering tests passed: evidence
flow now covers ordinary Python tools; relative paths, constructor components,
standard-library aliases, branch/setup state, unpacking, keyed containers,
comprehensions, glob patterns and positional-only arguments retain identity.
Parties now has separate canonical refusal and synthetic success exercises.
The original runner files were untouched by review fixes.

### 2026-11-22 — Review pass

Follow-up pass. Reviewers read the committed implementation diff since the
baseline (copy/rename-aware, this spec excluded except as the edge-case claims
file); patches below were then applied directly, because no step-03
implementation session existed to re-engage.

- verdicts: 49 findings — high 0, medium 24, low 18, false 7, maybe-false 0
- findings:
  - `FB1` `[medium]` `[patch]` Reconstructed evidence paths escape at load, execute and copy sinks — Probe: `runpy.run_path`, `spec_from_file_location`, `subprocess.run` and `shutil.copy` on `ROOT / ('_bmad-' + 'output')` returned no failure. Added standard-library read/copy/load/process sinks (child-process arguments only when constructed or absolute); a new control rejects all four.
  - `FB2` `[medium]` `[patch]` Spec-loaded and imported-class helpers are not followed — Probe: a `spec_from_file_location`/`module_from_spec` helper called with `ROOT` returned no failure; 18 tracked suites load modules that way. Spec-loaded local modules are now followed; new control. The imported-class-instance part is rejected as low: an AST scan found no production class that takes a root and reads `setup/` or `rendered/`, and instance modelling needs a new value type.
  - `FB3` `[medium]` `[patch]` A non-literal component erases the known path — Probe: computed and loop-built names, `with_suffix` and `open(file=...)` returned no failure. Unknown `/` and `Path(...)` components now stay wildcards under the known prefix, `with_suffix`/`with_stem` keep identity and keyword arguments reach sinks; new controls.
  - `FB4` `[low]` `[reject]` Unparsable or undecodable Python crashes the guard — It fails closed: the boundary test aborts instead of passing, no tracked Python is unparsable, and fixture copies under `/tests/` cause no false positive. A structured error path adds branches for a case nobody meets.
  - `FB5` `[low]` `[reject]` Line-based comment skipping can hide an evidence path in a string line starting with `#` — Needs a contrived multi-line string; tokenizer-based skipping is more than a direct correction.
  - `FB6` `[medium]` `[patch]` Default runner outputs vanish with `run-with-temp` — Folders prints only status lines, so its records disappear unless captured inside the wrapper. The README now states the cleanup, gives a capture example and notes that Parties prints its complete record, including messages.
  - `FB7` `[medium]` `[patch]` Reused Folders command logs no longer resolve beside the record — `verify-product-candidate.py:240,245` keep `attempt-1/…`/`attempt-2/…` while records now live in scratch. The README now names them as relative to story 17's original evidence directory; runner bytes stay path-only.
  - `FB8` `[low]` `[patch]` G-6 selectors come from a frozen CiCd projection while notes say "paths only" — The capture is a dated attempt-16 record whose 21 methods the runner already requires exactly; freezing is the approved disposition. Corrected the README row and the projects-publication relocation note.
  - `FB9` `[false]` `[reject]` Moved runners and fixture directory sets are unpinned — Nothing requires freezing intentional future edits; the path-only property is recorded by diff digest; an added fixture is still a tracked input under the evidence guard. No harm is named.
  - `FB10` `[low]` `[reject]` Story 20's handoff leads to a record naming the old verifier location — The live invoke note, runbook and architecture spine name the new path; `execution.md` is an immutable record whose sibling reference now fails visibly; EventStore preparation is already published. Editing another story's in-review spec is not a direct correction here.
  - `FB11` `[medium]` `[defer]` The relocated EventStore verifier suite is outside the tool-suite gate — `check_global.py:401-402` discovers only `tools/tests/test_*.py`. Pre-existing under `evidence/20`; it also needs a Builds-release prerequisite decision.
  - `FB12` `[medium]` `[defer]` Live procedures still name other evidence-resident executables — spec-23 names `evidence/23/read-preflight.py`; readiness READMEs invoke evidence scripts. Pre-existing: the removed sentence covered only the relocated runner sets. Resolution edits AGENTS.md or story 23 tooling.
  - `FB13` `[medium]` `[defer]` Parties exact-input checks vanish under `python3 -O` — Pre-existing bare asserts that the path-only rule forbids changing here.
  - `FB14` `[medium]` `[patch]` The exercise's Parties refusal and Projects fixture checks are weak — Mutation: removing the exact-byte assert still passed because the mode assert refused with an empty message. The refusal branch now requires the error to name the mismatched input, and the dead Projects exemption was deleted (Projects reads its fixture). The mutation now fails.
  - `FB15` `[false]` `[reject]` Host-specific credential paths are undocumented — The runbook already requires inspecting and adapting each runner before reuse; credential/account bindings are preserved runner policy; "output paths" was dropped because outputs are no longer hardcoded.
  - `FB16` `[low]` `[patch]` README and runbook omissions — Added the `tools/tests/` test location and noted that `conversations_fixture_results.py` is a separate qualifier. The runbook's Parties receipt link now targets the byte-identical fixture the runner reads.
  - `FE1` `[medium]` `[patch]` Constructed evidence paths passed to load/execute calls — Same defect as FB1; shared sink fix.
  - `FE2` `[low]` `[reject]` A tracked symlink into evidence is read through — The repository tracks no symlinks; detection adds a branch for an unmet case.
  - `FE3` `[low]` `[reject]` Unparsable Python aborts both boundary tests — Same as FB4; fails closed.
  - `FE4` `[medium]` `[patch]` `ROOT / Path(...)` loses the registry suffix — Probe returned no failure; `/` now accepts path-valued operands (FB3 fix); new control.
  - `FE5` `[medium]` `[patch]` Nested helper bodies are never analysed — Probe returned no failure. Nested definitions are now analysed with enclosing paths and callable with argument binding; new controls.
  - `FE6` `[medium]` `[patch]` Inherited setUp and class state are lost — Probe returned no failure; suites here inherit local harness bases (`Harness`, `Workflow`). Same-module bases now supply class state, setUp/setUpClass and inherited methods; new controls.
  - `FE7` `[low]` `[reject]` Subscript, walrus, with-as and starred bindings — Starred unpacking is already detected (probe). The others are uncommon registry-path carriers, each needing a new binding branch.
  - `FE8` `[low]` `[reject]` Reads inside `match` cases are skipped — No tracked suite uses `match`; case traversal is a new branch for an unused form.
  - `FE9` `[medium]` `[patch]` Live registry copies and existence checks pass — Probe: `shutil.copytree(ROOT / 'rendered', …)` and `os.path.exists(ROOT / 'setup')` returned no failure; shared sink fix; new control.
  - `FE10` `[medium]` `[patch]` Helpers loaded through `spec_from_file_location` are not followed — Same defect as FB2; shared fix.
  - `FE11` `[false]` `[reject]` Non-executable agent-tooling scripts are unchecked — The approved D1 classification the intent adopts places agent tooling in the prose/receipt class, and §4.1's test covers files outside that set; BMAD tooling reads its output tree by design.
  - `FE12` `[false]` `[reject]` Linked worktrees resolve the main checkout's module store — The original hardcoded the same store, so behaviour is unchanged; a missing pinned revision fails loudly at clone/checkout.
  - `FE13` `[low]` `[reject]` G-6 overwrites raw CTRF with its indented copy — The original also kept raw CTRF only in scratch, and the copy holds the same data; nobody needs the raw bytes, and a results directory would ripple into the exercise and recorded runner identity.
  - `FE14` `[low]` `[patch]` The exercise accepts CTRF files written by the controlled SDK — It now requires both files to be the runner's indented retained copies.
  - `FE15` `[low]` `[reject]` Ignored files are copied while HEAD's tree is recorded — Recorded qualifications use fresh clones without ignored files; archiving from Git adds machinery for a development-only case.
  - `FE16` `[low]` `[reject]` Unset or reused `TMPDIR` gives a traceback — Loud misuse failure; the README requires `run-with-temp`.
  - `FE17` `[low]` `[reject]` `--report` inside `TMPDIR` or in a missing directory — Operator error, contradicted by the option help; extra guards add branches.
  - `FE18` `[low]` `[patch]` Fixture-read classification inspects absolute path parts — It now inspects only parts relative to the copied qualification tree.
  - `FE19` `[medium]` `[defer]` The relocated EventStore suite is not discovered — Same as FB11.
  - `FE20` `[medium]` `[patch]` Reused Folders log references dangle — Same as FB7; README note.
  - `FE21` `[medium]` `[patch]` Evidence-boundary acceptance claim — The constructed-path load/execute bypass is fixed with FB1. The symlink and agent-tooling parts are rejected under FE2 and FE11.
  - `FE22` `[medium]` `[patch]` Registry-boundary acceptance claim — The Path-operand, nested, inherited, copy and spec-loaded bypasses are fixed (FB1–FB3, FE4–FE6, FE9, FE10). The subscript/walrus/with-as/match parts are rejected under FE7 and FE8.
  - `FE23` `[low]` `[reject]` Recorded source tree versus copied working-tree bytes — Same as FE15.
  - `FV1` `[medium]` `[patch]` Dropping `--path-format=absolute` from Folders `COMMON` would ship undetected — Pre-verified gap. Fake Git now prints a relative common directory unless absolute output is requested, and Folders product requires all five dependency clone sources to be absolute and inside the layout store. The mutation now fails on that assertion.
  - `FV2` `[medium]` `[patch]` Reused Folders log pointers point at nothing — Same as FB7.
  - `FV3` `[medium]` `[defer]` EventStore verifier tests are not in the normal gate — Same as FB11; the reviewer also notes it predates the change.
  - `FI1` `[medium]` `[defer]` Procedure surface versus non-prose guard (spec-23 evidence scripts under an unconditional AGENTS rule) — Same as FB12.
  - `FI2` `[low]` `[patch]` Path edits change input bindings — The selectors part is the same as FB8. `COMMON` keeps the original store (FE12), CTRF retention is FE13 and log names are FB7. The Parties field names a byte-identical, identity-pinned copy.
  - `FI3` `[false]` `[reject]` Controlled boundaries versus "same checks and results" — carried: as the prior controlled-exercise row records, the approved acceptance asks for disposable-input exercise of the actual bodies, and the record excludes product/publication acceptance; unexercised Projects flags touch no changed line.
  - `FI4` `[false]` `[reject]` Literal versus semantic evidence test — carried: as the prior literal-strings row records, the pinned identities are inert historical bytes, and freezing them is the documented design.
  - `FI5` `[low]` `[reject]` Child-process reads and the GlobalTests fixture change — Constructed or absolute child-process paths are now checked (FB1), and arbitrary reads by a child program are a static-analysis limit. The only `cwd=ROOT` suite reads `tools/qualification`. GlobalTests still runs the actual global runner with its bootstrap digest assertion; only unrelated live checks are mocked.
  - `FI6` `[medium]` `[patch]` Docs change beyond paths, outputs disappear, and the D1 prose set is duplicated ahead of 28-4 — Output loss is FB6's README fix; the receipt wording follows AGENTS Evidence; sharing the prose set belongs to 28-4 when `change_scope.py` exists.
  - `FI7` `[false]` `[reject]` The record is outside the diff — The diff deliberately excluded this spec, the edge-case claims file; the committed record holds the blob, fixture and qualification tables.

The 23 patch rows form 14 entries: 10 medium and 4 low. The guard fixes are in
`tools/repository_inputs.py`, covered by six new negative controls and one
disposable positive. The exercise fixes are in `exercise_relocation.py`; the
operator wording is in the qualification README, the runbook and the
projects-publication note. The six defer rows form three frontmatter entries.
Runner and fixture bytes are unchanged.

## Design Notes

The seven existing shared provenance files stay shared validation inputs. Exceptions identify exact immutable bytes containing non-followed receipt/module-source strings, never authorize a path read, and cannot hide a changed or additional dependency. This preserves proof hashes rather than rewriting historical identities to satisfy a textual scan.

Required fixture disposition: Folders registration config stays byte-identical; prior receipts can project only the consumed `{candidate, commands}` (attempts 1/2) and `{shared_classification}` (attempt 3). EventStore planned configuration stays byte-identical. Parties state, accepted receipt, normalization and whole patch stay byte-identical; the dynamic unit receipt may project `{dependencies}`. G-6's Projects-owned deterministic support fixture may project `{selectors}` (21 methods). Keep the original receipt records; record fixture source identities. The complete Parties patch is 1,583,039 bytes and contains inert deleted-source evidence paths; bind it by exact identity alongside the seven shared provenance inputs, never by a general fixture-directory exemption.

Use subagents for implementation components as useful, awaiting all results before returning. Build a reusable clean-checkout qualification exercise under `tools/`, with controlled external dependencies and disposable source inputs. Exercise actual runner bodies through relocated fixture/output paths; help-only or missing-source failures alone are insufficient.

Historical runners bind historical module revisions; relocation qualification uses disposable inputs and controlled external tools. It proves paths and preserved behavior, not fresh module readiness or authority to publish.

## Verification

- Run affected G-6 and relocated EventStore suites under `run-with-temp`.
- Run dependency guard with negative evidence-reference and real-root registry-read mutations.
- Exercise all relocated entry points in a clean candidate checkout with disposable inputs and controlled external boundaries; compare runner changes against original Git blobs to verify path-only edits.
- Record a compact result/digest plus full source commit/tree/blob IDs here; keep raw output in scratch.

### Relocation identities and fixture disposition

Implementation source is CiCd commit `539299f4800073aeaee52e98a0e596144ef34fe1`,
tree `60fb4163caa6c36c3173a5d5c194eae6fc43e73c`. The seven original runner/test
blobs below are retained in Git history. Old paths are relative to
`_bmad-output/specs/spec-cicd/evidence/`; new paths are relative to
`tools/qualification/`.

| Old path | New path | Old blob | New blob |
| --- | --- | --- | --- |
| `17/verify-product-candidate.py` | `pre-adoption/folders/verify-product-candidate.py` | `244bed6748564c94d32b437b7a0fad912ec281c0` | `7abb49401f4ec918eb4e63dfd16016a967dc720f` |
| `17/verify-final-candidate.py` | `pre-adoption/folders/verify-final-candidate.py` | `1f8a77ff244d86dcaab1226c914519c191d04a08` | `dfcd314063a008893ad9f719b6a71ed21762c62a` |
| `18/qualify-owning-g6.py` | `qualify-owning-g6.py` | `45150e2d534782f418d01b233070f9475cd046b8` | `370a39c8ad1c847926ad69ea6f9f87dcd8423b78` |
| `18/local-package-build.py` | `pre-adoption/projects/local-package-build.py` | `1c48f831c4f05f700cad03e6a82d3e270db17cee` | `f5d12017f4f4022369ab563d5531538588c653c0` |
| `20/pre-adoption-verify.py` | `pre-adoption/eventstore/pre-adoption-verify.py` | `2b10ee3bdcd3495665e64cbef82f3e4720cfc5ae` | `dad94c8b7c91325e25c83ab4c6c3ef29942d2134` |
| `20/test_pre_adoption_verify.py` | `pre-adoption/eventstore/test_pre_adoption_verify.py` | `5c471cd7397e42dbcb5c5eefc5d9abd1f0035f6f` | `3415accf0fc44214ab890e0307be196d6f66c3d5` |
| `21/publication/qualify-push.py` | `pre-adoption/parties/qualify-push.py` | `87c54bbdc4d5c0807d034bf283981f20fd848868` | `7f2cb821f05567c50b933605c24178895eb9dccf` |

Runner changes are limited to repository/Git-common-directory discovery,
relocated input paths and scratch output paths. Folders separates fixture reads
from `folders-product-results/` and `folders-final-results/` beneath `TMPDIR`.
Parties writes reports/messages to `parties-publication-results/` there. G-6
writes reports to its supplied scratch directory. Projects resolves G-6 from
its CiCd tools location, independently of the disposable Projects runtime root.
EventStore keeps its required explicit report outside its disposable `TMPDIR`.
No policy check, exact-source comparison, failure, product requirement or
publication approval changed.

The path-only unified comparison against the original seven Git blobs has
SHA-256 `8de78a3c85a5bc91c466a143e72d9b49cffd7c597cf32e54bc555ae9887721ae`.
It contains only these path/output changes. Raw comparison output remained in
wrapper scratch.

The fixture inventory follows. Source paths use the old evidence prefix above,
except the explicitly named Projects source. Fixture paths use the new tools
prefix. Original receipt records remain in place; projected fixtures retain
only the approved consumed fields.

| Source | Fixture | Disposition | Source blob | Fixture blob |
| --- | --- | --- | --- | --- |
| `17/registration-candidate/rendered/Hexalith.Folders/.github/hexalith-ci.json` | `pre-adoption/folders/fixtures/registration-candidate/rendered/Hexalith.Folders/.github/hexalith-ci.json` | Byte-identical | `b44ecdc08641437e50a014b7c4213dd96627432c` | `b44ecdc08641437e50a014b7c4213dd96627432c` |
| `17/attempt-1/product-verification.json` | `pre-adoption/folders/fixtures/attempt-1/product-verification.json` | Project `{candidate, commands}` | `fa946075102b7f3fe562c0e04b42989a1c3adbe0` | `b013a66b4e534f977d9622cb07731ace10159557` |
| `17/attempt-2/product-verification.json` | `pre-adoption/folders/fixtures/attempt-2/product-verification.json` | Project `{candidate, commands}` | `4655cd4bb60ec11edafb29f20391238b611dbfb5` | `cf8da26f2ac090c44ffca3926bfab9f7d6954d79` |
| `17/attempt-3/product-verification.json` | `pre-adoption/folders/fixtures/attempt-3/product-verification.json` | Project `{shared_classification}` | `65170b21e6de5c07f8f674218cbc163ae320d00a` | `50161d569b21be8be6ff99faf5a0c29504e5f3e9` |
| `20/planned-configuration.json` | `pre-adoption/eventstore/fixtures/planned-configuration.json` | Byte-identical | `450e1e9ec4e7a9d217f885817dc2bdd50d554856` | `450e1e9ec4e7a9d217f885817dc2bdd50d554856` |
| `21/current-preparation-state.json` | `pre-adoption/parties/fixtures/current-preparation-state.json` | Byte-identical | `5dff836693d10681abc61f169a2fb3bfd4b746a8` | `5dff836693d10681abc61f169a2fb3bfd4b746a8` |
| `21/accepted-local-verification.json` | `pre-adoption/parties/fixtures/accepted-local-verification.json` | Byte-identical | `0a1c77843cdcc8679edbc1b26d237efad92a0492` | `0a1c77843cdcc8679edbc1b26d237efad92a0492` |
| `21/current-preparation.patch` | `pre-adoption/parties/fixtures/current-preparation.patch` | Byte-identical, all 1,583,039 bytes | `ef78ce7d5a00c1b27884a566da5501347fee863d` | `ef78ce7d5a00c1b27884a566da5501347fee863d` |
| `21/publication/whitespace-normalization.json` | `pre-adoption/parties/fixtures/whitespace-normalization.json` | Byte-identical | `4949f3703e251f34752e964e62aeb8728bf62a79` | `4949f3703e251f34752e964e62aeb8728bf62a79` |
| `21/runs/20261116T191919Z-3711f8e4/unit-only-preparation.json` | `pre-adoption/parties/fixtures/runs/20261116T191919Z-3711f8e4/unit-only-preparation.json` | Project `{dependencies}` | `5e8f55712687222ef24ae402b2ade9476bbbacfb` | `c57e2ae9022e93852fd0752abe28febec39946d8` |
| Projects `_bmad-output/implementation-artifacts/qualification-evidence/g-6-runtime-toolchain-20261001/attempt-16/capture/deterministic-support.json` | `fixtures/deterministic-support.json` | Project `{selectors}`, exactly 21 methods | `25043ab85fd2f7af33052d3bacfaa296a1219515` | `06779b772da3b7bcb512db1e937bf90d72090ba4` |

The G-6 fixture source is Projects commit `2c1d7363e23add596d289184d68242bd0f752056`,
tree `91e8a2a546549569afeab967bc35f8e3451a7c07`. Every fixture projection was
compared with its original committed blob, and every whole-copy fixture was
compared byte for byte. `test_qualification_fixtures.py` pins all eleven
relocated fixture SHA-256 identities. Shared provenance inputs retain their
original bytes; their narrowly pinned exceptions never permit followed reads
from evidence.

### Initial affected checks

Both commands ran under `run-with-temp`, with raw logs discarded from wrapper
scratch after digesting. Clean candidate qualification is recorded separately
when the complete implementation snapshot is available.

| Invocation | Result | Raw log SHA-256 |
| --- | --- | --- |
| `python3 -B -m unittest discover -s tools/tests -p test_g6_host_ports.py -v` | 23 passed | `e87e50b70fe406beee45c903077a59690ce7b60109bed1c2684012135d0715f8` |
| `python3 -B -m unittest discover -s tools/qualification/pre-adoption/eventstore -p test_pre_adoption_verify.py -v` | 17 passed using immutable Builds release `fdda17c0a4538b0f7c99f813c20ca24b49006530` for loader/schema tests | `0d36ca357ecac0964f246ab1f10535e0fcb1d676af8be1878fd0dc710c5a354a` |

### Dependency boundary and supporting verification

`tools/repository_inputs.py` checks tracked non-prose inputs and keeps exact
SHA-256 exceptions for the seven named shared provenance inputs plus the whole
Parties patch. A changed file fails even if its old path strings were removed;
a copy at a new path gains no exception. The approved D1 prose paths and comment-only historical source text are
distinguished from active input reads; shared Markdown fixtures receive no
prose exemption. No directory of shared data or fixtures is exempted.

The registry check follows Python path identities through aliases, positional
and keyword helper/default arguments, local/imported helper functions and
constants, dynamically loaded local helpers, class methods and `os.path.join`.
It scans tracked test locations throughout `tools/`, including the relocated
EventStore suite. Disposable fixture roots remain valid. The analysis is static
and bounded; it does not claim to interpret arbitrary dynamically generated
Python or prove equivalence of unknown external code. Negative controls cover
ordinary direct, aliased and helper-based reads, and evidence-input additions,
changed/copied provenance and nested-suite relocation.

The guard identified one preexisting live-root consumer:
`GlobalTests.test_bootstrap_digest_failure_fails_actual_global_runner` accumulated
a bootstrap failure and continued into real registry checks. It now invokes the
same actual global runner with its existing disposable workspace fixture and
retains the bootstrap digest-failure assertion.

| Invocation under `run-with-temp` | Result | Raw log SHA-256 |
| --- | --- | --- |
| `python3 -B -m unittest discover -s tools/tests -p test_repository_inputs.py -v` | 16 passed, including evidence-reference and real-root registry mutations plus scratch positives | `acdcb55eb7b9b67995cb48939294bc806c074b2269803ab383e7c278ad08c001` |
| `python3 -B -m unittest discover -s tools/tests -p test_validate.py -v` | 54 passed | `319dcb59425bb5444e902093c6446b6d95aeac14a975c6ad7cacabdc15e122e2` |

`test_qualification_fixtures.py` passed its eleven frozen input comparisons;
`test_qualification_relocation.py` passed its complete controlled body exercise.
Those development runs preceded the final clean candidate snapshot. The reusable
exercise requires a clean checkout by default and records its full commit/tree,
fixture reads, output checks, log digests and explicit execution limits.

An additional development scan covered the union of tracked and intended new
files without staging the shared index: 8,390 candidate paths, zero evidence or
registry failures. Its compact result SHA-256 is
`8c390b83c0e6d048e4f929ae955f5e7f366dded7a30dc2cac8a1707750f3f631`.


### Clean candidate qualification

An isolated local Git snapshot was created from the staged candidate with
`git write-tree` / `git commit-tree` (no branch update), then cloned beneath
`run-with-temp`'s `TMPDIR` and checked out detached. Candidate commit
`e5860cc7e1f8c339d7cf5d35eb979e51691e5eff`, tree
`17fbdab67a4835774f439c04f60be4e399ab04f7`. Python 3.14.4 ran the commands
below. Only Builds was initialized from local objects, at the recorded gitlink
`3060b20abfcf4ea804ad31816d435e5c754fc129`; EventStore loader/schema cases read
release commit `fdda17c0a4538b0f7c99f813c20ca24b49006530`. No product module
was initialized. Checkout status was clean before and after all checks.

| Command from clean candidate, under wrapper scratch | Result | Log SHA-256 |
| --- | --- | --- |
| `python3 -B -m unittest discover -s tools/tests -p test_g6_host_ports.py -v` | 23 passed | `b33fee9d2a8b07053a813cdf3b0aa4d2408857b7ade09ddfb0d7ec8ad5c9c028` |
| `python3 -B -m unittest discover -s tools/qualification/pre-adoption/eventstore -p test_pre_adoption_verify.py -v` | 17 passed | `07f2def6376e1d769efe3081e653f8949a86f273783f0050f080ea15e4650e59` |
| `python3 -B -m unittest discover -s tools/tests -p test_repository_inputs.py -v` | 16 passed | `e4af8761df7f80c53cf3fc3f90535b28c1bda2f0690da935ddc4ee93715cb204` |
| `python3 -B -m unittest discover -s tools/tests -p test_qualification_fixtures.py -v` | 1 passed | `35dc21feef9a8e4be79568d5515d2ea62e7007dab0c552a9d49268a6ea5c0840` |
| `python3 -B -m unittest discover -s tools/tests -p test_qualification_relocation.py -v` | 1 passed | `d81b5c96c2d378bb1f16479be090381da340cbe2aba5f992c40457481971cb9f` |
| `python3 -B -m unittest discover -s tools/tests -p test_validate.py -v` | 54 passed | `f549e38fc15b7c6b7ab7e92f117ba7d720e77b09a31d6e905021e80d844d279b` |
| `python3 -B tools/qualification/exercise_relocation.py` | All six runner bodies and released-audit refusal exercised; `clean_checkout: true` | `229d5bc3aab8cad38bf78db93dd6bf32fef3cb30619bd5a73c4f86f7ba288e58` |

All eleven relocated fixture identities passed. Folders product/final read
3/2 fixtures and preserved failed/blocked outcomes; Projects and G-6 each read
the relocated selectors and verified scratch reports/container cleanup;
EventStore completed its preparation body with controlled external tools;
Parties read all five proof fixtures and verified dependency pins before the
intentional source-byte mismatch, then wrote its failed report in scratch.
These exercises establish relocation behavior and preserved checks, not real
product readiness, publication or hosted acceptance. Raw logs and module copies
were removed with wrapper scratch after all foreground work completed.

The matrix audit is satisfied by the body integration test (live consumer and
retained refusal), evidence mutation/provenance tests (evidence dependency), and
direct/aliased/local/imported/default-helper tests plus scratch positives
(registry dependency); every covering test ran and passed above.

During parent diff inspection the Markdown exemption was narrowed to the exact
approved D1 prose paths. New controls reject references even in shared Markdown
headings. The tools README's story link became a plain story identifier to keep
shared inputs free of evidence references. Runner bytes and fixture identities
were unchanged by this guard correction; clean requalification follows below.

Guard correction requalification used clean isolated commit
`5d60e8987e7c78038e9ab3734f7bd8571640b936`, tree
`c848e18cb6196471852e6ae93c9d813fb911bcda`, without initializing any
submodules. The same guard command passed all 16 tests (log SHA-256
`d04b5905f243639fd3153bca851bfb8fd5375d31a28a2ac3e299707fbd76c5be`),
and the same six-body/refusal entry-point exercise passed with clean checkout
true (log SHA-256
`0a5f3390207e4a34e06bb9358218f5e915d06960d445e46e89451d216a271b85`).
Final checkout status remained clean; scratch was removed.


### Final reviewed clean-checkout verification

The reviewed implementation was exercised from isolated commit
`2f07314927d283081e2f4e305f1d50146f3362a9`, tree
`4b2b4db0007b25cc7b31b83a888dbd47749e255c`, with Python 3.14.4. The same
private local clone procedure and Builds gitlink as the first qualification
were used; only Builds was initialized. All 122 tests passed. Guard execution
used the exact global-discovery interface
`uv run --locked --script --python <current-python> tools/tests/test_repository_inputs.py -v`
with `UV_NO_CACHE=1`; the other suite invocations were unchanged from the table
above. The 26-test guard suite completed in 29.359 seconds, below the global
runner's 600-second suite timeout.

| Check | Result | Log SHA-256 |
| --- | --- | --- |
| G-6 host ports | 23 passed | `b4e00ee7a5d58671a2bd4187d9508b3ae52554b65f2d4a4dc336e4cdca9d0598` |
| Relocated EventStore | 17 passed | `784a426cf29b54d1ac860747abe16e91a7ecc8ac2797a23e81cec25f37874052` |
| Dependency guard | 26 passed | `813a125404c03b5b9bc03f2bfa7b6fbce1691eb84c4a27f860f11f430845f2d7` |
| Frozen fixtures | 1 passed | `35dc21feef9a8e4be79568d5515d2ea62e7007dab0c552a9d49268a6ea5c0840` |
| Runner body integration | 1 passed | `da5a49b6f8e3a6b857fc04632c78ef0a128b9b175576950255eddd16253d5184` |
| Validation | 54 passed | `dc27fcc7db3db35532cdf9c2a84734b7adb1b6e01944fe82e67947f749155a48` |
| Clean entry-point exercise | Six runners, Parties success and released-audit refusal passed | `c2326b5b4ec42362ba955c692e28c06b8ee03f9011c60507e0401f7715769a56` |
| Parties output mutation | Moving messages from OUTPUT back to HERE correctly fails integration (exit 1) | `3c06a1eeac27caf5538f4ee70aa59cccf39291d4bec3f3d1cbbef4a6e38e6bde` |

Both Parties messages had their exact expected contents beneath
`$TMPDIR/parties-publication-results/`. Its success case uses synthetic
receipts/source only in a private copy; the canonical fixtures are separately
identity-checked and exercised through their exact-input refusal. Restoring
the mutation left the checkout clean. All foreground jobs finished before
wrapper cleanup. A parent portability check also passed the guard's scratch
positive with `TMPDIR` absent; it now uses its own temporary fixture root.
All seven runner/test blobs still match the original relocation identity table.
Copy-aware `git diff --find-renames --find-copies-harder --check` passed; the
whole historical patch was preserved rather than whitespace-normalized.

### Follow-up review verification

The follow-up patches were exercised from isolated candidate commit
`2bb18bbec004a96fbcba77071a7eccb3778eb2e9`, tree `cb2cdcbdfdbde547de8f1429f9315904b28d9828`. The candidate was built with a private index
(`git commit-tree`, no ref update), cloned beneath `run-with-temp`'s
`TMPDIR` and run with Python 3.14.4. Only Builds was initialized, from local
objects at gitlink `3060b20abfcf4ea804ad31816d435e5c754fc129`; release
`fdda17c0a4538b0f7c99f813c20ca24b49006530` was available for the EventStore
loader/schema cases. Checkout status was clean before and after. All 129 tests
passed.

| Check | Result | Log SHA-256 |
| --- | --- | --- |
| G-6 host ports | 23 passed | `e87e50b70fe406beee45c903077a59690ce7b60109bed1c2684012135d0715f8` |
| Relocated EventStore | 17 passed | `d9e674c85f2c53b55c2170567323a13b6c4933d0bd941678e4faf3128d77c97a` |
| Dependency guard (`uv run --locked --script`, `UV_NO_CACHE=1`) | 33 passed in 47.4 s | `8e23473c2e1921da445790c8a44499cab9dd7ea8bdac02372340b1eb31b1f6b0` |
| Frozen fixtures | 1 passed | `35dc21feef9a8e4be79568d5515d2ea62e7007dab0c552a9d49268a6ea5c0840` |
| Runner body integration | 1 passed | `ae687f73b105b37647b79fb560dc83a4f699acbd96a70b0496f138a3d49c41e3` |
| Validation | 54 passed | `c39e5ed0241692dd2b7723d1815c0a69460d02628dc0ef83cf1ec03df0724433` |
| Clean entry-point exercise | Eight exercises passed, `clean_checkout: true`; fixture reads 3/2/1/1/1/5/5/3 | `7ef59ae3ee360954d1f88e78e7be0e5787814c608a82e7c2945f44ee4c621fbd` |

The guard also reports zero evidence and registry failures for the real
repository. Its suite time rose from 29.4 s to 47.4 s, against the global
runner's 600 s suite timeout.

Mutation controls ran on private copies of `tools/qualification` from the
development checkout:

| Mutation | Result | Log SHA-256 |
| --- | --- | --- |
| Parties exact-byte assert removed | Exercise fails: refusal was not the exact-byte check | `6f5e2d53296d413d72ef77a27730bf4a3b2ae492c7bfab7aba1082d3b3862c5c` |
| Parties unmutated | Exercise passes; error names `Directory.Solution.targets` | `2f4769c09fb64690031243808892c29a50a202b72302388568c6b2aad452e28b` |
| Folders `--path-format=absolute` removed, relative store resolvable | Exercise fails: dependency clones left the CiCd module store | `cebc8b5e85701080e584e6d31ffdcda4ffb96e2f4f142e6de0ab4e083115dd7a` |
| Folders unmutated, same layout | Exercise passes | `ec37b03e11d80c27a1cc0622e35471941a80335a98f4d2bcbddd48e229288edd` |

All seven runner/test blobs still match the relocation identity table, and all
eleven fixtures are unchanged. Raw logs and clones were removed with wrapper
scratch after all foreground work finished.

## Auto Run Result

Status: done.

Story 28-3 moved the seven named executable runner/test files and their eleven
active fixtures out of evidence into `tools/qualification/`. Runner bytes
changed only for paths and scratch outputs. It added tracked-evidence and
live-registry boundary tests, and recorded blob identities and clean-checkout
qualification. This follow-up pass hardened the boundary analysis, tightened the
relocation exercise and completed the operator documentation. Runner and
fixture bytes are unchanged.

Files changed in this pass:
- `tools/repository_inputs.py` — standard-library read/copy/load/process sinks, wildcard path components, nested and inherited fixture analysis, spec-loaded helper following.
- `tools/tests/test_repository_inputs.py` — six negative controls for those bypasses and one disposable-fixture positive.
- `tools/qualification/exercise_relocation.py` — the following:
  - realistic `--git-common-dir` output with clone-source assertions;
  - an exact-byte Parties refusal check;
  - a check that the runner retained the CTRF files;
  - fixture classification relative to the copied tree;
  - removal of a dead Projects exemption.
- `tools/qualification/README.md` — the following:
  - output capture before wrapper cleanup;
  - what the reused Folders log names refer to;
  - where the G-6 selectors come from;
  - a note that the fixture-result qualifier is separate;
  - the full test path.
- `docs/pre-adoption-publication.md` — the Parties receipt link points at the byte-identical fixture the runner reads.
- `_bmad-output/implementation-artifacts/spec-fix-projects-publication-gates.md` — the relocation note states the selector source change.
- This story — follow-up triage, deferred items, verification identities and results.

Review findings: 49 (high 0, medium 24, low 18, false 7, maybe-false 0).
- **Patched:** 23 rows in 14 entries; by entry verdict, high 0, medium 10, low 4.
- **Deferred:** 6 rows in 3 entries:
  - the EventStore suite is outside the tool-suite gate;
  - live procedures still name other evidence-resident executables;
  - the Parties bare asserts vanish under `-O`.
- **Rejected:** 20 rows, with reasons in the triage log:
  - FB4/FE3: the guard fails closed, and no tracked Python is unparsable.
  - FB5: needs a contrived `#` line inside a string.
  - FB9: no harm named.
  - FB10: live references are updated; the record is immutable and fails visibly; preparation is published.
  - FB15: covered by the runbook's inspect-and-adapt rule.
  - FE2: no tracked symlinks.
  - FE7/FE8: uncommon binding forms; starred unpacking is already caught.
  - FE11: approved D1 prose class.
  - FE12: unchanged store semantics, with a loud failure.
  - FE13: the same data as the original durable copy.
  - FE15/FE23: recorded runs use fresh clones.
  - FE16/FE17: loud operator misuse.
  - FI3/FI4: carried false rows.
  - FI5: a static child-process limit; GlobalTests keeps its assertion.
  - FI7: the record was deliberately excluded from the diff.

Follow-up review recommended: false. This was a follow-up pass and patched no
high entry.

Verification: the affected G-6, EventStore, guard, fixture, integration and
validation suites (129 tests) and the clean entry-point exercise passed from
isolated candidate `2bb18bbec004a96fbcba77071a7eccb3778eb2e9`. Mutation controls showed that the Parties
exact-byte and Folders clone-source checks now fail when broken. Identities and
digests are under Follow-up review verification above.

Residual risks:
- The path analysis is still static and bounded. It does not model subscript, walrus, with-as or match bindings, imported class instances, reflection, generated code or arbitrary reads by child programs. Every probed ordinary form passes, as do all current tracked inputs and the real repository.
- Guard suite time rose to about 47 s.
- The three deferred items remain open.
- Story 28-4 should reuse this prose classification rather than duplicate it.
- No fresh module product qualification, hosted CI or publication was performed or claimed.
