---
title: '13 — Migrate Works (Discovery Follow-Up & Closeout)'
type: 'feature'
created: '2026-11-28'
status: 'done'
route: 'dispatch'
baseline_commit: '9ada4b8a87e128e1b811944e13d1e79017941446'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/specs/spec-cicd/stories/13-migrate-works.md'
  - '{project-root}/_bmad-output/specs/spec-cicd/enforcement.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Works is adopted (`v2.0.0` immutable, `ci` + `platform-parity` passed on `fe369b7a` / `v6.9.2`, CodeQL + release passed in Nightly `45985698522`). Platform moved the four non-Works lanes (`f035498b`, pinned at `7eaa9eb8`), dropping hosted scan `45995012594` from 43 files / 130 diagnostics to 21 files / 19 diagnostics (17 Platform + 2 Works, 0 duplicates). Nightly acceptance still fails on those 19 diagnostics, and AD-21 legacy Zot cleanup remains open.

**Approach:** Execute Step 3 of the Works Platform discovery plan under Option A: add generalizable CiCd scanner rules (plus reviewed-export Git handling for `works_host_snapshot.py:65`), qualify the scoped Works `verify-source-debug.py` `configparser` candidate locally, hand off the remaining 8 Platform sites, and stop before final Story 13 closeout while AD-21 legacy Zot remains open.

## Boundaries & Constraints

**Human decisions (2026-11-28):**
1. **Discovery scope (Option A):** Add generalizable CiCd scanner rules (safe Git `inspection_environment()`, literal `os.environ` allowlist dict-comp, imported/forwarded safe `env`, `dotnet nuget verify`, read-only `argv` logging/formatting in forwarded wrappers, Windows `taskkill /PID <pid> /T /F`, reviewed-export `works_host_snapshot.py:65`); prepare the scoped Works candidate replacing `git config --file .gitmodules` with stdlib `configparser` (hold locally unless exact-base hosted CI + hosted scan pass); hand off the remaining 8 Platform sites (`bound_builds.py:71`, `builds_tuple.py:93`, `retained_works_host.py:30`, `verify_works_host.py:1044`, `prepare_builds_artifacts.py:122`, `works_toolchain.py:77`, `isolated_daprd.py:50`, `works_verifier_command.py:87`).
2. **AD-21 Zot (Option A):** Legacy Zot cleanup remains open; skip maintainer-profile readbacks and stop before Story 13 `done` closeout after scanner, Works candidate, and evidence/handoff updates.

**Always:** Preserve prior `13-migrate-works.md` decisions, R1–R11 parity, `verify-source-debug.py` behavior, and fail-closed discovery (`-c`, `git config`, `hook`, `submodule foreach`, aliases, computed verbs/binaries, unsafe paths, and resolution-affecting env vars keep failing). Use CiCd-agent for CiCd, module-agent for Works PRs, `run-with-temp` for disposable jobs, and compact `< 256 KiB` receipts under `evidence/13/`.

**Never:** Edit owned Works files. Weaken audits, tests, or fail-closed scan checks. Run maintainer-profile readbacks. Import owned CI/CD via PR Update branch.

## I/O & Edge-Case Matrix

| Scenario | Input | Expected Behavior | Error Handling |
| --- | --- | --- | --- |
| Safe Git env | Helper/dict stripping `GIT_*` and setting only `GIT_NO_REPLACE_OBJECTS`/`GIT_NO_LAZY_FETCH`/`GIT_OPTIONAL_LOCKS` (direct, imported, forwarded) | Accepted as safe `env` | Reject other `GIT_*` (`GIT_EXEC_PATH`, `GIT_SSH*`, `GIT_CONFIG*`), `PATH`, `PYTHON*`, `DOTNET_*`, `LD_*`/`DYLD_*` |
| Env allowlist | `{k: v for k, v in os.environ.items() if k in ALLOWED}` with literal set | Accepted as safe `env` | Reject non-literal set, value transforms, or added keys |
| Read-only tool/wrapper | `dotnet nuget verify <path> --all`; `taskkill /PID <pid> /T /F`; wrapper storing `argv` in local dict or `{argv!r}` | Cleared; literal script operands still enter discovery | Fail on computed verb/binary, tracked shadow, or escaping/mutating `argv` |
| Reviewed export | `eng/works_host_snapshot.py:65` under `WORKS_PLATFORM_EXPORT` | Cleared when SHA-256 matches | Fail `unproved` on any byte drift |
| Forbidden ops | `-c`, `git config`, missing `--end-of-options`, `os.execv`, computed binary | Fail loudly with line diagnostic | Never downgrade outside `unittest` test boundary |

</frozen-after-approval>

## Code Map

- `tools/scan_discovery.py` -- `copied_environment` L4139, `environment_copy` L3683, `environment_key` L3637, `GIT_ENV_PREFIXES` L237, `forward_wrapper` L4877, `sequence_read` L4848, `git_data_argv` L4420, `fixed_dotnet_argv` L4705, `WORKS_PLATFORM_*` L165–214.
- `tools/tests/test_scan.py` & `docs/duplicate-scan.md` -- Works boundary tests (`L3745–3949`), rule tests, and discovery contract (`L149–260`).
- `references/Hexalith.Works/scripts/verify-source-debug.py` -- L67 `execute`, L78 `taskkill`, L137 `git config --file .gitmodules`; live `main` `5d5b56e1` (Platform `7eaa9eb8`, Builds `v6.9.2`).
- `references/Hexalith.Platform/eng/` (`7eaa9eb8`) -- 9 cleared (`bound_builds.py:31,41,46`, `builds_tool_lock.py:104`, `builds_tuple.py:72,86`, `current_catalog_view.py:126`, `prepare_builds_artifacts.py:22`, `works_host_snapshot.py:65`); 8 handed off (`bound_builds.py:71`, `builds_tuple.py:93`, `retained_works_host.py:30`, `verify_works_host.py:1044`, `prepare_builds_artifacts.py:122`, `works_toolchain.py:77`, `isolated_daprd.py:50`, `works_verifier_command.py:87`).
- `_bmad-output/specs/spec-cicd/stories/13-migrate-works.md` & `evidence/13/` -- Story 13 record and compact receipts.

## Tasks & Acceptance

**Execution:**
- [x] `tools/scan_discovery.py` -- Add safe Git `inspection_environment()` (direct, imported, forwarded conditional `env`), literal `os.environ` allowlist dict-comp, `dotnet nuget verify`, Windows `taskkill /PID <pid> /T /F`, read-only `argv` logging/formatting in forwarded wrappers, and reviewed-export Git calls in `WORKS_PLATFORM_EXPORT` -- Clears 9 Platform sites and `verify-source-debug.py:78`.
- [x] `tools/tests/test_scan.py` & `docs/duplicate-scan.md` -- Add positive and adversarial bypass tests for every new rule and document them -- Locks fail-closed behavior.
- [x] `references/Hexalith.Works/scripts/verify-source-debug.py` -- Prepare behavior-preserving `configparser` candidate; verify local discovery and standalone `check.py` under `run-with-temp`; hold locally until exact-base hosted scan/CI permit PR push -- Clears Works-owned diagnostics locally.
- [x] `_bmad-output/specs/spec-cicd/evidence/13/` & `stories/13-migrate-works.md` -- Record local before/after scan on `5d5b56e1`, hosted CI status, 8-site Platform handoff, held Works candidate receipt, open AD-21 Zot prerequisite, and update Story 13 -- Preserves exact revision/digest receipts.

**Acceptance Criteria:**
- Given Works `main` (`5d5b56e1`, Platform `7eaa9eb8`), when local production `scan.scan()` runs without executing module code, then Platform diagnostics drop from 17 to 8 (exact handed-off sites) and Works diagnostics drop from 2 to 1 (`verify-source-debug.py:67` -> L137 `git config`), with 0 run errors and 0 duplicates.
- Given the local Works candidate replacing L137 `git config` with `configparser`, when scanned locally and verified via standalone `check.py`, then Works diagnostics drop to 0 and `check.py` exits 0; the candidate stays local until hosted scan covers exact Works `main` at the updated scanner revision.
- Given the scanner changes, focused scanner tests and `tools/render.py --check` exit 0 under `run-with-temp`, forbidden overrides (`-c`, `git config`, `GIT_EXEC_PATH`, tampered `works_host_snapshot.py`, unproved binaries) still fail loudly, and no raw or `> 256 KiB` evidence is added.

## Implementation Notes

- Implemented all six generalizable fail-closed scanner rules in `tools/scan_discovery.py` (uncommitted working-tree blob `751c54e4da14a31c3adae9690efe23106f46da98` on `c31df42a`), documented them in `docs/duplicate-scan.md` (blob `2f62412b62b631bcd181a6cdb5feb9046c7e2e4c`), and added positive + adversarial bypass tests in `tools/tests/test_scan.py` (blob `18bef3e0b09c4a1c91645535ce980eac539b96a8`).
- Verified `run-with-temp uv run --locked --script tools/render.py --check` (exit 0) and 89 locked scanner tests including all new rules and Works boundary/export-drift tests (exit 0, SHA-256 `d1e7bce6249757330054b0667c7c443e09e1b9ca19ac082be36f862bd3ddb70a`).
- Verified local production `scan.scan()` on Works `main` (`5d5b56e1`, Platform `7eaa9eb8`): 19 -> 9 diagnostics (exact 8 handed-off Platform sites + 1 Works site `verify-source-debug.py:67` -> L170 -> L137 `git config`), 21 files, 0 run errors, 0 duplicates.
- Prepared held local Works candidate `ba908c0b102295317b4c24cd4d92fd66b77769fb` on local branch `fix/works-source-debug-configparser-5d5b56e1` in `references/Hexalith.Works` (working tree left cleanly on `main` `5d5b56e1`, not pushed). Verified 0 Works diagnostics (8 Platform + 0 Works, 0 run errors, 0 duplicates), 20/20 `test_source_debug_verification.py` tests passing, and standalone `python3 references/Hexalith.Builds/check.py` exit 0 (386 ArchitectureTests, 3 PropertyTests, 603 UnitTests, clean checkout).
- Recorded compact receipt (`_bmad-output/specs/spec-cicd/evidence/13/discovery-followup-20261128.md`) and updated Story 13 (`status: blocked` retained while AD-21 legacy Zot cleanup, hosted scanner requalification, and the 8-site Platform handoff remain open).

## Spec Change Log

## Review Triage Log

### Pass 1 (2026-11-28) — Blind Hunter (13), Verification Gap (5 + 5), Edge Case Hunter (24)

- `[high]` `[patch]` (BH-1) `tools/scan_discovery.py:6077-6271`: `exported_proofs` and `env_helper_proofs` loops finish before `forwarded_env_proofs` calls `copied_environment` without `exports=...` and appends new `env_helper_proofs`. Verified in code; real bypass.
- `[high]` `[patch]` (BH-2) `tools/scan_discovery.py:2891-2895,6130-6225`: Direct-name re-export (`from callee import f` in `reexport.py`, called from `evil.py`) stops in `name_reachers` at L2895 without traversing `reexport.py`'s importers. Verified in code; real bypass.
- `[high]` `[patch]` (BH-3) `tools/scan_discovery.py:6098-6118`: `env_helper_proofs` only checks direct `importers.get(def_path)`, `ast.Attribute` Store/Del, and positional constant `patch.object`, missing string `patch('mod.fn')`, keyword `attribute=`, non-constant `patch.object`, and transitive importers. Verified in code; real bypass.
- `[high]` `[patch]` (BH-4) `tools/scan_discovery.py:3722-3765,5091-5136`: Module-level `literal_string_set` omits `exported_proofs`, and `is_property_listcomp` checks only same-file `Attribute`/`Subscript` Store/Del, missing `.update()`/escapes and importer rebinding/mutation. Verified in code; real bypass.
- `[high]` `[patch]` (BH-5) `tools/scan_discovery.py:5425-5474`: `safe_sink` approves `records.append(record)` on an unproved parameter/call result whose `.append` can mutate `record['command']` before `subprocess.Popen`. Verified in code; real bypass.
- `[high]` `[patch]` (BH-6) `tools/scan_discovery.py:5263-5285`: `dotnet_nuget_verify_argv` allows a computed operand alongside extra non-flag literals (e.g. `[dynamic_flag, 'evil.config']`) and accepts non-string constants in `non_literal`. Verified in code and via `dotnet nuget verify` probe; real bypass.
- `[high]` `[patch]` (BH-7) `tools/scan_discovery.py:5068-5089,5175-5181`: `is_option_flag` accepts arbitrary `f"-{dynamic}"` strings, and `is_property_expr` omits `Global`/`Nonlocal` checks. Verified in code; real bypass.
- `[medium]` `[patch]` (BH-8) `tools/scan_discovery.py:3020-3024,3185,6155`: `python_context[path]` is stored before `sys.path`-proven roots are appended at L3185, omitting them during `forwarded_env_proofs`. Verified in code.
- `[medium]` `[patch]` (BH-9) `tools/scan_discovery.py:5937-5938,6273-6278`: `TASKKILL_EXECUTABLES` check is not deferred to the end of `discover()` for pinned submodules acquired later. Verified in code.
- `[medium]` `[patch]` (BH-10) `tools/scan_discovery.py:3700-3721,4437-4479,4521-4524`: `resolve_local_module` clamps out-of-root `..` relative imports to `.`; `copied_environment` skips single-binding check on `scope.name`; `forwarded_environment` passes caller `cwd`/`roots` instead of `target_path`'s context and misses `import mod; mod.fn`. Verified in code.
- `[medium]` `[patch]` (BH-11) `tools/scan_discovery.py:1318-1324`, `tools/tests/test_scan.py:4190-4232`: `works_platform_export_context` omits `cwd == "."`, and its test lacks `__pycache__` and wrong-action negative cases. Verified in code.
- `[low]` `[patch]` (BH-12) `discovery-followup-20261128.md:1861,1897-1898`: Evidence should explicitly state that listed scanner/test/doc blobs are uncommitted working-tree edits on top of `c31df42a` and record broader non-timeout tool verification. Verified in diff.
- `[low]` `[patch]` (BH-13) `docs/duplicate-scan.md:172,223`: Doc states `{argv!r}` and literal `set`, while code accepts any `FormattedValue` without `format_spec` and `set`/`frozenset`/`tuple`/`list`. Verified in code.
- `[medium]` `[patch]` (VG-1) `tools/tests/test_scan.py`: Pre-verified gap — missing negative tests for `fixed_msbuild_properties` local list mutations/escapes, extended `--artifacts-path`, and invalid/mutated `DEPENDENCIES` comprehensions.
- `[medium]` `[patch]` (VG-2) `tools/tests/test_scan.py`: Pre-verified gap — missing copied-environment `DOTNET_ENV_PREFIXES` and computed-`cwd` negative tests for `dotnet nuget verify`.
- `[medium]` `[patch]` (VG-3) `tools/tests/test_scan.py`: Pre-verified gap — missing `discover_boundary` tests for `env_helper_proofs` and `forwarded_env_proofs` (clean boundary test vs workflow-command-file test vs unresolved import).
- `[medium]` `[patch]` (VG-4) `tools/tests/test_scan.py`: Pre-verified gap — missing positive/negative tests for `import env_helper`/`import callee` attribute calls, positional env forwarding, and monkeypatched imported env consumers.
- `[medium]` `[patch]` (VG-5) `tools/tests/test_scan.py`: Pre-verified gap — missing negative tests (`mutate_prefix`, `escape_prefix`, `rebind_prefix`) for local prefix lists in `forwarded_argv`.
- `[high]` `[patch]` (VG-O1) `tools/scan_discovery.py:6098-6271`: Loop-order bypass where `forwarded_env_proofs` appends to `env_helper_proofs` after its loop ran (same root cause as BH-1). Verified.
- `[high]` `[patch]` (VG-O2) `tools/scan_discovery.py:6249-6255`: `forwarded_env_proofs` omits `exports` check for callers (same root cause as BH-1). Verified.
- `[high]` `[patch]` (VG-O3) `tools/scan_discovery.py:5110-5117`: `is_property_listcomp` misses `.update()`/escape and cross-module mutations (same root cause as BH-4). Verified.
- `[high]` `[patch]` (VG-O4) `tools/scan_discovery.py:5435-5457`: Unproved `.append()` sink parameter in `sequence_read` (same root cause as BH-5). Verified.
- `[high]` `[patch]` (VG-O5) `tools/scan_discovery.py:6109-6117`: String-target `patch('mod.fn')` and module escape bypass `env_helper_proofs` (same root cause as BH-3). Verified.
- `[high]` `[patch]` (EC-1) `tools/scan_discovery.py:5922`: `fixed` can be empty at L5897 (`subprocess.run([])`), crashing with uncaught `IndexError` on `fixed[0]`. Verified in code at L5897-5922.
- `[high]` `[patch]` (EC-2) `tools/scan_discovery.py:6098-6271`: Loop-order bypass & missing `exports` (same root cause as BH-1). Verified.
- `[high]` `[patch]` (EC-3) `tools/scan_discovery.py:4521-4546`: `forwarded_env_proofs` accepts `*args`/`**kwargs` (`vararg`/`kwarg`) parameters as subprocess `env`, letting `f(PATH='.')` bypass proof. Verified in code.
- `[high]` `[patch]` (EC-4) `tools/scan_discovery.py:4474-4482`: `Global`/`Nonlocal` declaration for `parameter.arg` in `forwarded_environment` causes `scope_reads` to return `[]` and approve arbitrary mutations. Verified via `resolving_scope` L3615.
- `[high]` `[patch]` (EC-5) `tools/scan_discovery.py:5554-5561`: `Global`/`Nonlocal` declaration for callback `param.arg` in `wrapper_callers` causes `scope_reads` to return `[]` and skip all callback calls. Verified via `resolving_scope` L3615.
- `[high]` `[patch]` (EC-6) `tools/scan_discovery.py:3787-5557`: Nested `ClassDef` body causes `resolving_scope` (L3621) to return `None`, omitting class-body reads/mutations from `scope_reads` proofs. Verified in code.
- `[high]` `[patch]` (EC-7) `tools/scan_discovery.py:5435-5457`: Unproved parameter sink in `sequence_read` (same root cause as BH-5). Verified.
- `[high]` `[patch]` (EC-8) `tools/scan_discovery.py:5085-5117`: Mutable/imported `is_property_listcomp` dict (same root cause as BH-4). Verified.
- `[medium]` `[patch]` (EC-9) `tools/scan_discovery.py:5097-5107`: `is_property_listcomp` omits `conversion == -1` and `format_spec is None` check on `FormattedValue`. Verified in code.
- `[high]` `[patch]` (EC-10) `tools/scan_discovery.py:5160-5163`: `--artifacts-path` local list omits `not isinstance(initial.elts[1], ast.Starred)` check. Verified in code.
- `[high]` `[patch]` (EC-11) `tools/scan_discovery.py:5062-5070`: `is_property_expr` local name resolution omits `Global`/`Nonlocal` check (same root cause as BH-7). Verified.
- `[high]` `[patch]` (EC-12) `tools/scan_discovery.py:5276-5285`: `dotnet nuget verify` option injection (same root cause as BH-6). Verified.
- `[high]` `[patch]` (EC-13) `tools/scan_discovery.py:3933-3946`: `import pkg.helper` without alias resolves `pkg/helper.py` when code calls `pkg.inspection_environment()`. Verified in code.
- `[medium]` `[patch]` (EC-14) `tools/scan_discovery.py:3730-3733`: Relative import level exceeding directory depth clamps to root (same root cause as BH-10). Verified.
- `[high]` `[patch]` (EC-15) `tools/scan_discovery.py:3679-3722`: `parse_python_source` omits assignment-alias propagation (`m = os`), so `environment_source_proved` misses aliased `m.environ` mutations in cross-module proofs. Verified in code.
- `[high]` `[patch]` (EC-16) `tools/scan_discovery.py:6098-6118`: `env_helper_proofs` misses string `patch`, keyword `attribute=`, and module escapes (same root cause as BH-3). Verified.
- `[high]` `[patch]` (EC-17) `tools/scan_discovery.py:6158-6195`: `forwarded_env_proofs` omits single-binding check on `func_name` in `def_path` and misses `from . import func` (`entry.module is None`). Verified in code.
- `[high]` `[patch]` (EC-18) `tools/scan_discovery.py:3781-3793`: `literal_string_set` allows chained `in` comparisons (`len(parent.ops) > 1`) and omits `exported_proofs` for module-level names (shares root cause with BH-4). Verified.
- `[high]` `[patch]` (EC-19) `tools/scan_discovery.py:5541-5652`: `wrapper_callers` omits `exported_proofs` when a nested wrapper is passed to a module-level `helper` that an importer can monkeypatch. Verified in code.
- `[low]` `[patch]` (EC-20) `tools/scan_discovery.py:5853-5870`: Dead `properties` branch in `direct_python_call` unreachable after `fixed_dotnet_argv` returns at L5835. Verified in code.
- `[high]` `[patch]` (EC-21) `tools/scan_discovery.py:6098-6271`: Claim finding matching BH-1/EC-2 (loop-order bypass). Verified.
- `[high]` `[patch]` (EC-22) `tools/scan_discovery.py:5435-5457`: Claim finding matching BH-5/EC-7 (unproved sink parameter). Verified.
- `[high]` `[patch]` (EC-23) `tools/scan_discovery.py:5276-5285`: Claim finding matching BH-6/EC-12 (`dotnet nuget verify` option injection). Verified.
- `[high]` `[patch]` (EC-24) `tools/scan_discovery.py:3781-3793`: Claim finding matching BH-4/EC-18 (allowlist export & chained `in`). Verified.

## Verification

**Commands:**
- `run-with-temp uv run --locked --script tools/render.py --check` -- exit 0
- `run-with-temp uv run --locked --script tools/tests/test_scan.py` (focused + Works boundary tests) -- exit 0
- Local `scan.scan()` before/after on `5d5b56e1` and local Works candidate under `run-with-temp` -- 19 -> 9 on `main`, 8 Platform + 0 Works on candidate, 0 run errors, 0 duplicates
- `run-with-temp python3 references/Hexalith.Builds/check.py` in disposable Works candidate checkout -- exit 0
