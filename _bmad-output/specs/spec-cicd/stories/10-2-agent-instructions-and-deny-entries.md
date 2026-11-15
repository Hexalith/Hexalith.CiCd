---
title: 'Agent instructions and deny entries'
type: 'chore'
created: '2026-11-15'
status: 'ready-for-dev'
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

- [ ] `templates/partials/ownership-block.txt.j2` — replace the placeholder with the ownership and product-first rules above, accurate fresh-main guidance and the human-decided Update branch restriction. Keep the body module-agnostic and free of marker delimiters.
- [ ] `templates/partials/deny-entries.json.j2` — use effective `Edit` path denials for whole-owned workflow/config files and Builds subtree. Protect partial-entry portions through instructions and the guard without claiming file-tool rules can target JSON keys or marker ranges. Keep reads available and settings project-local; document launching the agent from module root.
- [ ] `tools/tests/test_render.py` — update existing policy expectations; exercise adding required denies, preserving foreign settings/text, missing-owned-content drift, repair and repeated no-op application. Keep invalid-template cases and add no workflow-text assertions.
- [ ] `AGENTS.md`, `setup/README.md` — record the product-gate classification and final policy ownership; include the user's `run-with-temp` instructions verbatim in the new root guidance.
- [ ] `references/Hexalith.AI.Tools/hexalith-llm-instructions.md` — replace merge-triggered release advice and link to the canonical CiCd ownership template. Add the narrow exception to its outside-folder-link restriction required by this story; avoid agent-entrypoint link cycles. Preserve CRLF and use the restricted module token for its validated commit/push.
- [ ] `references/Hexalith.AI.Tools` gitlink and this story — record the remotely reachable guide revision, verification and dependency disposition; render/check without adding production registrations.

**Acceptance Criteria:**

- Given enabled policy templates, when fixture output is applied to existing module content, then all three blocks and required denies converge while foreign content survives.
- Given module CI failure or a refused update, when an agent follows the delivered policy, then it fixes product failures or reports pipeline/refusal issues without editing owned portions or escalating credentials.
- Given the final guide and CiCd guidance, when their CI/CD advice is read, then they identify the same ownership contract, product-only gates and nightly release model.

## Implementation Notes

## Spec Change Log

## Review Triage Log

## Design Notes

Claude's current file rules match `Edit(path)` for writes; `Write(path)` is accepted syntactically but does not match. Project `/path` rules anchor at the primary working directory, so instruct starting at module root. File-level rules cannot distinguish owned marker/JSON portions; the shared guard remains the enforcement for those portions. [Official permission documentation](https://code.claude.com/docs/en/permissions#read-and-edit).

## Verification

- `run-with-temp uv run --locked --script --python 3.12 tools/tests/test_render.py` and runner Python equivalent — rendering and shared-library preservation/repair pass.
- Wrapped `tools/render.py --check` and existing validation suite — no production registry or rendered drift.
- Check guide link target, preserved CRLF and root instructions; validate the exact AI.Tools commit message with its pinned commitlint before any push.
