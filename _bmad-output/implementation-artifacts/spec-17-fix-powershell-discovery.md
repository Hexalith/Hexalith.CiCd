---
title: '17 — Fix PowerShell script discovery'
type: 'bugfix'
created: '2026-11-16'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

Correct CiCd discovery of ordinary PowerShell syntax and literal script calls
blocking story 17. Preserve failure on unresolved dynamic execution and all
security checks; add focused regressions, rerun the saved minimal and exact
Folders reproductions, and record remaining diagnostics. Work from freshly
fetched main in an isolated worktree, preserving existing workspace edits.
Use `run-with-temp` for disposable verification. Keep the separate migration
story in progress until its audit, product and adoption prerequisites pass.

</frozen-after-approval>

## Implementation Notes

- Isolated branch `fix/17-powershell-discovery` starts at current main
  `2adf156b24e0a8053de42d7d4bf9b7c15a8b82e4`. The main shared workspace and other story worktrees
  are read-only inputs. No remote publication is requested.
- Code map: `tools/scan_discovery.py` currently applies Bash structure checks
  and `shlex` to PowerShell. Add inert PowerShell AST parsing and reuse
  `segment`, `include`, `targets` and source diagnostics. The parser must never
  evaluate module text and must fail closed if missing or unsuccessful.
- `tools/tests/test_scan.py`: qualify ordinary declarations/control flow and
  literal calls; preserve dynamic invocation, environment, cwd, process,
  reflection and interpreter failure checks. Replace the invalid isolated
  `else` fixture with complete valid PowerShell control flow.
- Update the PowerShell parsing contract and runtime prerequisite in
  `docs/duplicate-scan.md`. Save before/after Folders selection and complete
  diagnostics under `evidence/17/`, and append a narrow resume note. Keep the
  existing migration spec status and acceptance boxes unchanged.
- No intent gaps or irreversible operations; bounded change to discovery,
  tests, documentation and evidence. Use the oneshot route for this defect,
  independently of story 17's migration acceptance.
- Implementation: added fixed `tools/scan_powershell.ps1` AST projection and
  Python event validation/traversal. Source enters the parser only as stdin;
  missing/failed/timed-out parsers and malformed events fail coverage. Require
  PowerShell 7 for reachable PowerShell sources. Literal fallback remains
  independent of invocation recognition, including arrays and local module
  requirements. Unsupported method/property operations remain explicit failures.
- Native parser refinement: use its checked `ModuleAnalysis` API, which avoids
  post-parse host module/type resolution. Git blob discovery supplies module
  resolution instead. Tests prove an existing local module is not executed and
  a missing host module causes no lookup-dependent parser error; incompatible
  runtimes fail closed.
- Saved reproduction: exact baseline matches 940 diagnostics and 12 files;
  minimal now has zero diagnostics; corrected Folders has the same 12 files and
  318 diagnostics. Full inventory and hashes are under
  `../specs/spec-cicd/evidence/17/powershell-discovery/`. Existing migration spec
  status and acceptance boxes are unchanged.

## Review Triage Log

- High, patched: computed command operands could evade execution checks when
  their AST source was forwarded as literal text. Validate complex operand
  shapes before command handling; regressions cover unknown launchers and
  parenthesized Python execution text.
- High, patched: argument splatting hid dynamic operands without a dollar sign.
  Project and reject the AST splatting flag; regression uses `unknown-launcher @Arguments`.
- High, patched: attached parameter expressions bypassed execution-text checks.
  Preserve the AST type of attached parameter operands; regressions cover
  parenthesized and variable `Invoke-Expression -Command:` operands.
- High, patched: coalescing and other assignment operators escaped regex-only
  environment checks. Inspect assignment targets and operators; regressions
  cover indexed and `??=` writes, including PATH.
- High, patched: unary environment mutation was absent from assignment events.
  Inspect prefix/postfix increment/decrement; sensitive variables fail while
  local counter increments remain valid ordinary syntax.
- High, patched: computed pipeline input to `Invoke-Expression` supplied no
  visible execution operand. Reject missing/pipeline-fed evaluation text;
  regression uses concatenated path fragments piped to evaluation.
- Medium, patched: malformed parser events could raise uncaught key errors.
  Validate all event shapes; malformed JSON/events, subprocess failures and
  timeouts have focused fail-closed regressions.
- High, patched: local `#requires -Modules` dependencies were omitted. Traverse
  parser requirements; regression proves dynamic execution in a required local
  module still fails.
- Medium, patched: reproduction baseline followed HEAD and would change after
  commit. Pin the full fetched pre-fix main identifier and compare it against
  saved files and diagnostics exactly.
- High, patched on recheck: alias cmdlet/provider mutation could redirect a
  harmless-looking command into evaluation. Fail command-resolution mutation
  explicitly, with cmdlet and provider regressions, including copy/move/rename
  aliases, alias imports and PSDrive changes. The provider guard recognizes
  mutation verbs and their short aliases.
- Medium, patched on recheck: valid module-specification hashtables emitted
  null parser text and lost traversal. Extract literal ModuleName operands;
  unsupported values fail explicitly without discarding other literal events.
- Medium, patched on recheck: literal attached `pwsh -Command:` arguments were
  mistaken for stdin-fed execution. Normalize attached values into typed
  operands; positive literal-call regression preserves dynamic-operand failures.

## Verification

- Full scanner suites: 109 tests passed on each of the default interpreter and
  Python 3.12, including all pinned-detector qualification. After final review
  corrections, 12 focused checks and the added provider-mutation regression
  passed on Python 3.12. No skipped tests. Commands, outputs and hashes are in
  `../specs/spec-cicd/evidence/17/powershell-discovery/qualification.json`.
- Saved minimal reproduction: two prior diagnostics become zero. Frozen
  baseline Folders reproduction exactly matches saved 940 diagnostics; final
  scanner retains the same 12 files with 318 explicit coverage failures.
- Production render passes with the pinned direct Builds revision in a
  disposable copy. The fresh worktree's initial direct check failed because
  Builds was uninitialized; no submodules were initialized in this worktree.
- Original migration spec, production setup/render, workflows and module
  gitlinks are unchanged. Story 17 remains in progress. All review findings
  were patched; no deferred findings remain for this defect.
