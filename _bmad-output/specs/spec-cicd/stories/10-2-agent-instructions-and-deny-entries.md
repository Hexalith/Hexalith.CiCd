---
title: 'Agent instructions and deny entries'
type: 'chore'
created: '2026-11-15'
status: 'done'
baseline_commit: '46532c7d9647f2bc2e852c935ab0857c83931ed0'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/specs/spec-cicd/enforcement.md'
  - '{project-root}/_bmad-output/specs/spec-cicd/gate-classification.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Rendered ownership instructions and Claude denies are placeholders; the shared guide still describes releases on merge. Agents lack the agreed CI/CD ownership and gate rules before pilot adoption.

**Approach:** Replace the two policy partials, document the gate rule in CiCd, update AI.Tools' shared guide, and verify rendering, preservation and repair through the existing perimeter engine.

## Boundaries & Constraints

**Always:** State that CiCd owns workflows, CI config, Dependabot, Builds gitlink/section and delivered instruction/deny portions. Require fixing the product, reporting pipeline defects, successful `python3 references/Hexalith.Builds/check.py` before pushing, no workflow-YAML assertion tests, no audit/test bypasses, no skip markers/trailers, and product branches from freshly fetched current main. Record only verified branch findings. User authorized this prerequisite and required provisioning on 2026-11-15.

**Never:** Represent the refused PR-fixture creation as an Update branch result, broaden credentials, add machine-wide denies, change module owned files directly, or adopt a module in this story. Preserve foreign instruction text and settings. Follow the user's disposable-workspace instructions.

**Human decision, 2026-11-15:** Accept 10-1's three verified outcomes and cleanup for this handoff. Defer meaningful Update branch to story 11, with its probe branch/PR created before real delivery and updated afterward. Deliver the temporary instruction: do not use PR Update branch until the CiCd pilot verifies it; report refusals without switching credentials.

## I/O & Edge-Case Matrix

| State | Expected result |
| --- | --- |
| Render a fixture module | Three equal ownership block bodies and a unique, nonempty deny string list; markers supplied by engine. |
| Foreign instructions/settings exist | Keep foreign text, allow/deny entries and unrelated settings while adding owned policy. |
| Remove owned text or deny | Detect drift, repair through the shared library and converge idempotently. |
| Update branch not qualified | State the limitation explicitly; never claim a verified permission result. |

</frozen-after-approval>

## Code Map

- `templates/partials/{ownership-block.txt,deny-entries.json}.j2`: canonical block body and JSON list, embedded by `tools/render.py:desired_tree` and `templates/perimeter.json.j2`.
- `tools/tests/test_render.py:723` and `:945`: interim assertions and real shared-library fixture covering foreign text/settings and idempotence.
- Builds tagged `Github/lib/perimeter_config.py`: unique string denies; block body excludes ownership markers.
- `AGENTS.md`: absent; retain supplied disposable-workspace instructions when creating it.
- `setup/README.md`: remove interim-policy descriptions; preserve registry semantics.
- `references/Hexalith.AI.Tools/hexalith-llm-instructions.md`: root authoring restriction and obsolete release-on-merge paragraph. Existing guidance is CRLF.

## Tasks & Acceptance

**Execution:**

- [x] `templates/partials/ownership-block.txt.j2` — replace the placeholder with the ownership and product-first rules above, accurate fresh-main guidance and the human-decided Update branch restriction. Keep the body module-agnostic and free of marker delimiters.
- [x] `templates/partials/deny-entries.json.j2` — use effective `Edit` path denials for whole-owned workflow/config files and Builds subtree. Protect partial-entry portions through instructions and the guard without claiming file-tool rules can target JSON keys or marker ranges. Keep reads available and settings project-local; document launching the agent from module root.
- [x] `tools/tests/test_render.py` — update existing policy expectations; exercise adding required denies, preserving foreign settings/text, missing-owned-content drift, repair and repeated no-op application. Keep invalid-template cases and add no workflow-text assertions.
- [x] `AGENTS.md`, `setup/README.md` — record the product-gate classification and final policy ownership; include the user's `run-with-temp` instructions verbatim in the new root guidance.
- [x] `references/Hexalith.AI.Tools/hexalith-llm-instructions.md` — replace merge-triggered release advice and link to the canonical CiCd ownership template. Add the narrow exception to its outside-folder-link restriction required by this story; avoid agent-entrypoint link cycles. Preserve CRLF and use the restricted module token for its validated commit/push.
- [x] `references/Hexalith.AI.Tools` gitlink and this story — record the remotely reachable guide revision, verification and dependency disposition; render/check without adding production registrations.

**Acceptance Criteria:**

- Given enabled policy templates, when fixture output is applied to existing module content, then all three blocks and required denies converge while foreign content survives.
- Given module CI failure or a refused update, when an agent follows the delivered policy, then it fixes product failures or reports pipeline/refusal issues without editing owned portions or escalating credentials.
- Given the final guide and CiCd guidance, when their CI/CD advice is read, then they identify the same ownership contract, product-only gates and nightly release model.

## Implementation Notes

- Replaced both policy placeholders. The module-agnostic body identifies every
  whole and partial ownership boundary, product-gate rule, required successful
  pre-push check, no-bypass rule, fresh-main branch rule and provisional PR
  Update branch restriction. The engine still supplies marker delimiters.
- Delivered four unique project-local `Edit` denies: workflows, CI JSON,
  Dependabot and the Builds subtree. No read denies or machine-wide settings
  were added. The block and setup/root guidance explain module-root launching
  and that partial JSON/instruction/gitmodules ownership needs the shared guard.
- Extended the existing real tagged-library fixture to merge missing denies
  without duplicating an existing required deny, retain foreign allow/deny
  entries and unrelated settings, detect a removed block, changed block body
  and removed deny, repair them, then apply repeatedly without index changes.
  Existing invalid-template qualification remains; no workflow-text assertions
  were added.
- Created root `AGENTS.md` with the gate classification and the user's
  disposable-workspace instructions verbatim. Removed interim-policy advice
  from `setup/README.md`; the production registry remains empty.
- Published the shared guide at
  [`7ef8166ef87e1365f86d1a1b3aaf0235545177d4`](https://github.com/Hexalith/Hexalith.AI.Tools/commit/7ef8166ef87e1365f86d1a1b3aaf0235545177d4),
  changing only `hexalith-llm-instructions.md`. Its 369 line endings remain CRLF.
  It links directly to the canonical CiCd template through a narrow authoring
  exception, describes nightly releases and the same ownership/product-gate
  contract, and removes the conflicting `NuGetAudit=false` fallback. The exact
  full commit message passed pinned commitlint 21.2.4 before commit and push.
  Fetch, push, `ls-remote` and GitHub commit API verification used the protected
  restricted module token; the default CiCd-agent profile was preserved.
- Dependency disposition: the human accepted 10-1's three actual results and
  cleanup for this handoff. Product-only fresh-main push succeeded; a workflow
  push and valid dispatch were refused. Meaningful PR Update branch and Pull
  requests write remain unverified. The refused historical-workflow fixture
  creation is not an Update branch result. Story 11 must create the product-only
  probe branch/PR before real delivery, attempt its meaningful update after
  delivery advances main, repeat fresh-main branching, record actual responses
  and clean up. The temporary prohibition remains until that qualification.

## Spec Change Log

## Review Triage Log

- Parent matrix audit found that comparing rendered block bodies only with the
  template did not independently enforce row 4's provisional Update branch
  limitation. The existing final-policy test now checks every rendered body
  directly for the prohibition until pilot verification and the explicit
  unverified permission behavior. No workflow-YAML assertions were added.

All three context-free review layers completed. Edge-case review returned `[]`;
verification-gap review returned no gaps. Each blind-hunter finding was verified
and classified separately before grouping:

| ID | Verdict | Evidence and disposition |
| --- | --- | --- |
| B1 | medium | AI.Tools' own entry points require the shared guide, but AI.Tools has no Builds checkout or `.gitmodules`; the guide's new unconditional pre-push command cannot run there. Defer the standalone-tooling scope clarification because its fix edits agent-context instructions. |
| B2 | medium | The shared guide's CI/CD section prohibits credential switching while its Git section names `hexalith-git-instructions.md` as the source of truth; that file allows the maintainer fallback for an explicitly requested interactive push to an uncovered repository. Module-specific precedence should be explicit. Defer the instruction-file correction. |
| B3 | low | The guide includes package publishing in its push/PR CI bullet, while `tools/render.py` emits publishing in the release caller and separately documents nightly release orchestration. This is a wording defect, not changed workflow behavior. Defer the instruction-file correction. |
| B4 | low | The canonical block does not enumerate the perimeter's forbidden release/commitlint config, package entries, hook lines, response files and `bmad-testarch-ci` paths. The unchanged guard rejects/reconciles them, but a fuller instruction list would avoid rediscovery. Defer the generated agent-context documentation follow-up. |
| B5 | low | Other policy clauses are present and were checked against the approved intent; only the matrix's Update branch state has a separate semantic assertion. Additional clause-by-clause text assertions would guard hypothetical future edits rather than a current wrong output. Reject this unlikely everyday regression proposal because it adds duplicated text checks rather than a direct correction. |
| B6 | false | Tagged Builds already qualifies missing positive partial files and the same `/permissions/deny` pointer. The parent additionally exercised missing file, missing `permissions` and missing `deny` with four required values: all were created correctly and foreign values survived. See `../evidence/10-2/review-dependency-probe.json`. The enabled-policy fixture separately verifies multi-value insertion and deduplication. |
| B7 | high | Reproduced on unchanged Builds `v5.2.2`: `_marker()` replaces the entire file for unbalanced or duplicate markers, removing foreign prefix/suffix. Tagged tests explicitly assert that behavior. Defer this pre-existing dependency issue; it needs resolution before relying on preservation for malformed pilot input. No production module was adopted here. |
| B8 | low | The guide and template currently agree on ownership, required checks, credential refusals and nightly release behavior; static verification records the guide blob/link and review checked their content. A cross-repository semantic drift test is a future safeguard with no current mismatch. Reject the unlikely everyday regression proposal because it adds a separate text-comparison mechanism. |

B1–B4 have distinct documentation causes and B7 is an unchanged dependency
defect; each received its own deferred-work entry. B5, B6 and B8 were rejected
on the evidence above. No review patch or spec loopback was required.

## Design Notes

Claude's current file rules match `Edit(path)` for writes; `Write(path)` is accepted syntactically but does not match. Project `/path` rules anchor at the primary working directory, so instruct starting at module root. File-level rules cannot distinguish owned marker/JSON portions; the shared guard remains the enforcement for those portions. [Official permission documentation](https://code.claude.com/docs/en/permissions#read-and-edit).

## Verification

- `run-with-temp uv run --locked --script --python 3.12 tools/tests/test_render.py` and runner Python equivalent — rendering and shared-library preservation/repair pass.
- Wrapped `tools/render.py --check` and existing validation suite — no production registry or rendered drift.
- Check guide link target, preserved CRLF and root instructions; validate the exact AI.Tools commit message with its pinned commitlint before any push.

Implementation evidence is saved in `../evidence/10-2/`:

- `render-python312.log`: all 32 renderer tests passed on Python 3.12 in 27.738s.
- `render-python314.log`: all 32 renderer tests passed on Python 3.14 in 28.868s.
- `render-check.log`: wrapped render reported zero changed paths and `--check`
  succeeded with no production registrations.
- `render-python312-initial.log`: the initial simultaneous interpreter runs
  encountered a missing `jinja2` import in the shared uv script environment.
  Sequential runs with `UV_CACHE_DIR` under each wrapper's private `$TMPDIR`
  resolved it without changing dependencies or locks.
- `render-python314-initial.log`: an initial new assertion incorrectly required
  a fully removed marker block to return at its old position. The shared library
  appends a missing block while preserving foreign text. The assertion now
  checks preservation and canonical convergence, with repeated byte-stable
  no-op application.
- `ai-tools-commitlint.log`, `ai-tools-commit-message.txt` and
  `guide-verification.json`: exact-message validation, the unchanged pinned
  dependency/config input and CRLF/template-link checks. Temporary npm files
  were confined to the wrapper's `$TMPDIR` and removed at exit.
- `auth-preflight.json`, `auth-status.txt`, `repo-permissions.txt`,
  `ai-tools-fetch.txt`, `ai-tools-prepush-fetch.txt`, `ai-tools-push.txt`,
  `ai-tools-remote-main.txt` and `ai-tools-remote-commit.json`: intended profile,
  override presence, authenticated account, target, read-only metadata and actual
  successful restricted-credential publication. Account `admin: true` is not
  treated as evidence of token API permissions.
- `candidate-validation.json` and `validate-python314.log`: full existing
  validation passed, exit 0, verdict `{"global":true,"modules":[]}`. All 389
  tests across 14 tool suites passed, alongside committed-input/render checks,
  schema/caller checks, immutable-bootstrap qualification, acceptable Builds
  publication and workflow lint. Validation ran on disposable committed
  candidate `957c30be66a17e8fd9d5163710607724ebca77d7` from root baseline
  `46532c7d9647f2bc2e852c935ab0857c83931ed0`, with the five implementation
  code/docs files and published AI.Tools gitlink overlaid. Mutable story notes
  and evidence were outside that candidate scope. No root working-tree staging
  or commit was needed; the wrapper removed the candidate after completion.
- `final-verification.json`: at the first handoff, candidate source hashes
  matched the implementation; the frozen intent and verbatim disposable instructions were
  intact; guide working-tree, committed and remote bytes are equal and CRLF;
  the canonical template link resolves to its expected repository path;
  production registrations remain zero; rendered files and the Builds gitlink
  are unchanged; the default CiCd-agent profile and absence of inherited token
  overrides remain unchanged. Root diff whitespace checks passed. A plain
  AI.Tools diff check initially classified the required carriage returns as
  trailing whitespace; its CRLF-aware check
  (`git -c core.whitespace=cr-at-eol diff --check`) passed without changing line
  endings.
- `render-python312-follow-up.log` and `render-python314-follow-up.log`: after
  the parent audit's targeted policy-invariant assertions, all 32 renderer tests
  passed sequentially on Python 3.12 in 24.870s and Python 3.14 in 24.859s. Both
  commands used `run-with-temp` with a private uv cache under `$TMPDIR`.
- `follow-up-verification.json`: the full validator's successful result belongs
  to the prior candidate above. The only subsequent source change is the
  targeted assertion in `tools/tests/test_render.py`, covered by both follow-up
  renderer runs. All other candidate source hashes are unchanged. The broad
  validator was not repeated because no implementation concern was introduced.
  Parent staged entries were preserved; follow-up edits remain unstaged.

The guide is published; the final CiCd template, documentation, review results
and evidence are included in the local story commit. `root-commitlint.log` and
`root-commit-message.txt` record exact-message validation using the locked
commitlint 21.2.4 CLI and guard policy from Builds revision
`73e60af8a1fcdf3f06726d5d1b6e1199cce778ee`, extracted under `run-with-temp`.
The canonical URL already exists on CiCd `main`, which will serve the final
body after the root change is published. No production module was registered
or adopted. Meaningful PR Update branch qualification remains intentionally
assigned to story 11. Five review follow-ups are recorded in the deferred-work
ledger, including the pre-existing malformed-marker preservation risk to settle
before relying on preservation for malformed pilot input.


## Story 11 policy qualification — 2026-11-16

The actual two-pilot result supersedes the temporary unverified wording outside
this story's historical frozen contract. GitHub accepted both meaningful Update
branch operations with the same restricted credential and imported the real
delivered owned trees. Fresh-main product pushes also succeeded after normal
shared checks; both probe PRs closed without merging and all probe refs were
removed. [Story 11's exact proof](../evidence/11/post-delivery-update-branch.json)
and [cleanup](../evidence/11/product-probe-cleanup.json) retain revisions and
server responses.

The factual canonical policy now prohibits using Update branch to import owned
CI/CD changes and directs agents to current-main branches with only product
changes reapplied. It states the verified server allowance, without claiming a
refusal or banning unrelated product-only updates. The corresponding template,
renderer policy assertions and generated perimeters are authored in CiCd;
qualification and actual redelivery remain tracked by story 11. No module-owned
block, machine-wide deny or token permission was edited directly.

The completed updated-PR checks additionally establish a compatibility limit:
Codacy passed on both server merge heads, but the mandatory commit-format guard
rejected their service-generated `Merge branch 'main' ...` subjects with
`subject-empty` and `type-empty`. Product build/test stages did not run on those
probe merges. This is an observed operation/input result, not a token refusal or
product-code regression. [Exact messages and failed-job logs](../evidence/11/post-update-pr-failure-evidence.json)
are retained; the strict guard, closed PRs and cleaned refs remain unchanged.

The qualified scoped rule is now published in CiCd commit
`3427f041c5f686c460c1fa027cf6f835791209c1` and actually redelivered by successful
run `43869480499`; both resulting module trees and final-main CI are verified.
See [authenticated policy redelivery](../evidence/11/authenticated-policy-redelivery.json)
and [final CI proof](../evidence/11/final-main-ci-proof.json). Story 11 remains
in progress solely for its genuine scheduled-night checkpoint.
