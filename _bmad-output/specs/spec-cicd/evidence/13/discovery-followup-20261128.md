# Works discovery follow-up, local candidate and Platform handoff, 2026-11-28

## Exact inputs

- **CiCd controller:** baseline `9ada4b8a87e128e1b811944e13d1e79017941446`; current `HEAD` `c31df42ac893e52c3b566083f7e410680e5e6cec`. The following hashes are uncommitted working-tree edits on top of `c31df42a`:
  - `tools/scan_discovery.py` blob `751c54e4da14a31c3adae9690efe23106f46da98`
  - `tools/tests/test_scan.py` blob `18bef3e0b09c4a1c91645535ce980eac539b96a8`
  - `docs/duplicate-scan.md` blob `2f62412b62b631bcd181a6cdb5feb9046c7e2e4c`
- **Works `main`:** `5d5b56e11eafb121d688fea6f8523fa03863c676`, tree `91066b89b2b18d75a47ce58891695f237666c1e6`.
  - Pinned Platform gitlink: `7eaa9eb85d060b6d0d0c836a938ccb6e8795fa89`, tree `b476da7362a9f587e07f172ae76dea36d591e849`.
  - Delivered immutable Builds `v6.9.2`: `bb38c3e42f48f37de76c77983e4de83d99f619b7`.

| Works source (`5d5b56e1`) | Git blob |
| --- | --- |
| `.github/workflows/ci.yml` | `2f3034ef5fa48fea952c19c1c158b9e6dc0f4b02` |
| `.github/actions/platform-parity/action.yml` | `f9f3b0c6a104542748fe74ecac58396b54b9ef1b` |
| `scripts/prepare-platform-builds.py` | `828c0fd10edbe70285fb697af75e21c25d19702f` |
| `scripts/verify-platform-parity-ci.py` | `3da6f5ab2dd67658c913b21783015e896ebbfb78` |
| `scripts/verify-source-debug.py` | `9aaea5d83ed38adb40657807f8795e37a06a620b` |
| `scripts/tests/test_source_debug_verification.py` | `bc9ac9377418fa3c6369ee0fcac6dd599d9db323` |

## Hosted CI, Nightly and scan status

- Works is adopted (`v2.0.0` immutable). Both `ci` and `platform-parity` passed on `fe369b7a` / Builds `v6.9.2`, and CodeQL + release passed in Nightly `45985698522`.
- Platform moved the four non-Works lanes (`f035498b`, pinned in Works at `7eaa9eb8`), dropping hosted scan `45995012594` from 43 files / 130 diagnostics to 21 files / 19 diagnostics (17 Platform + 2 Works, 0 duplicates).
- Hosted requalification of the scanner changes below waits for CiCd `main` publication and the normal hosted scan workflow.

## Scanner changes and verification

Added generalizable fail-closed rules to `tools/scan_discovery.py` and documented them in `docs/duplicate-scan.md`:

1. Safe Git `inspection_environment()` stripping `GIT_*` and setting only literal `GIT_NO_REPLACE_OBJECTS`, `GIT_NO_LAZY_FETCH`, `GIT_OPTIONAL_LOCKS` (direct, imported zero-argument helper, and cross-module forwarded conditional `**({"env": env} if env is not None else {})` verified across all discovered callers and protected against importer mutation).
2. Read-only literal `os.environ` allowlist dict comprehensions (`{k: v for k, v in os.environ.items() if k in ALLOWED}` over a literal read-only set, rejecting non-literal sets, mutations, value transforms and added keys).
3. Fixed read-only `dotnet nuget verify <path> <safe-flags...>` (standard `subprocess`, tracked `dotnet` and `global.json` guards, rejecting computed verbs/binaries, `--configfile`, multiple computed operands, shell, `preexec_fn`, and `DOTNET_*` env).
4. Windows `taskkill /PID <pid> /T /F` (literal switch orders, standard `subprocess`, tracked `taskkill` executable guard, rejecting computed binaries/switches, shell, `preexec_fn` and unsafe env).
5. Read-only `argv` formatting (`{argv!r}`) and local non-leaking record-dict storage in forwarded wrappers, nested wrapper callbacks passed to proved direct-call local helpers, once-bound local prefix lists (`[*prefix, ...]`), `diff` `--binary`/`--no-renames`, and proved local MSBuild property/option lists (`--artifacts-path`, `-p:Name=Value`, literal-dict property comprehensions) with trailing options.
6. Reviewed-export Git wrapper callsite `(references/Hexalith.Platform/eng/works_host_snapshot.py, 65, subprocess.check_output)` cleared only when `WORKS_PLATFORM_EXPORT` SHA-256 matches and no `__pycache__` is present; any byte drift fails `unproved`.

Verification under `run-with-temp` (post-review-patch tree `751c54e4` / `18bef3e0` / `2f62412b`):

- `run-with-temp uv run --locked --script tools/render.py --check` — exit 0.
- `run-with-temp uv run --locked --script tools/tests/test_scan.py` (all 8 non-PowerShell unit test classes — `LauncherDiscoveryTests`, `TestBoundaryTests`, `UnittestEnvironmentProofTests`, `ImportIndexTests`, `NameReachTests`, `ReviewedProofGapTests`, `ComputedProcessContextTests`, `ErrorSourceTests` — plus Works boundary, reviewed-export drift, and MSBuild `ScanTests`) — **84 passed, 0 failed**.
- All other 32 locked tool test suites (`tools/tests/test_*.py` excluding `test_scan.py`) — **32/32 passed, 0 failed**.

## Local production `scan.scan()` comparison

All three runs used the production `scan.scan()` controller with local Git transports, zero module code execution, verified jscpd `5.4.3` signatures, and policy SHA-256 `abd8c8ad7ad31d1b315f6fe73742e410b245016f0b63c6ceabecc8615c41ffd8`. All three runs recorded **0 run-level errors**, **0 duplicates**, **0 observations**, **21 selected Works files**, and pinned Platform `7eaa9eb85d060b6d0d0c836a938ccb6e8795fa89`.

| Run | Controller | Works revision | Diagnostics | Files SHA-256 | Errors SHA-256 | Report SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| Before (`main`) | `9ada4b8a` (unmodified) | `5d5b56e1` | 19 (17 Platform + 2 Works) | `a34b512e3d10ffa394177f20d5f8a436713bef556554bf9c1a28d9e8b0ef4c09` | `47e604879e095341e37fbcc7dc04ccd71bf9a52975b2ab30d6f171f90088bb26` | `d745f80b6e6434c3a98e6814a708c00b08916d2fdc55e1909a88f4f3f78730c2` |
| After (`main`) | `c31df42a` + patched scanner (`751c54e4`) | `5d5b56e1` | 9 (8 Platform + 1 Works) | `a34b512e3d10ffa394177f20d5f8a436713bef556554bf9c1a28d9e8b0ef4c09` | `9b71409fcfa5ba0e6b8f6851af8968ce3cbe9cd19abc1a0cb412d4d9a904d360` | `f2d95c10e4d874d3cee1977b1a1650074f7e11c6913362dd15626f8bb86661ba` |
| After (Works candidate) | `c31df42a` + patched scanner (`751c54e4`) | `ba908c0b` | 8 (8 Platform + 0 Works) | `6c32304d5bc48a56eeb79c489e2470badefc9abdc88247caa82b9c58e4faa7ed` | `159013d24e88600345dd793e04146a03a97128e0d1c6e688b4cbaacef573561a` | `60d3b5f2d01bd1828d43d284d0c6ba832e1424561ead820b8cef9178edee72f1` |

Cleared sites (10 total on `5d5b56e1`):
- Platform (9): `eng/bound_builds.py:31,41,46`, `eng/builds_tool_lock.py:104`, `eng/builds_tuple.py:72,86`, `eng/current_catalog_view.py:126`, `eng/prepare_builds_artifacts.py:22`, `eng/works_host_snapshot.py:65`.
- Works (1 on `main`): `scripts/verify-source-debug.py:78` (`taskkill`); `scripts/verify-source-debug.py:67` narrowed to a single diagnostic naming L170 -> L137 (`git config`), which drops to 0 on the held Works candidate.

## Held local Works candidate receipt

Prepared on local branch `fix/works-source-debug-configparser-5d5b56e1` in `references/Hexalith.Works` from `5d5b56e11eafb121d688fea6f8523fa03863c676` (superproject checkout kept cleanly on `main` `5d5b56e1`; **not pushed**):

- **Candidate commit:** `ba908c0b102295317b4c24cd4d92fd66b77769fb`, tree `4a1821c84bea098979d4d4b674a57d66b0de9d8b`.
- **Changed files (product-owned only; zero owned CI/CD edits):**
  - `scripts/verify-source-debug.py` (blob `59f5f0666065cee6adde8454f1da4243c1e7b4cc`) — replaces L137 `git config --file .gitmodules --get-regexp` in `source_owners` with stdlib `configparser.ConfigParser(interpolation=None)`, preserving exact section/path validation and failure behavior.
  - `scripts/tests/test_source_debug_verification.py` (blob `95d194a7c3eab9203e929d9deff0c68b09f18f88`) — writes `.gitmodules` in `exercise_pipeline` fixture and removes the obsolete `git config --file` mock branch.
- **Works unit tests (`test_source_debug_verification.py -v`):** 20/20 passed in 3.277s in disposable standalone checkout with all 15 direct submodules; output SHA-256 `0f56394aadc43cebb7b01c6a720f83cd344d0b7dcbc872846ca14d72751de520`.
- **Standalone `python3 references/Hexalith.Builds/check.py` (Builds `v6.9.2`):** exited 0 in disposable standalone checkout with all 15 direct submodules at recorded gitlinks; guard policy passed, 0 README findings, Release build 0 errors, ArchitectureTests 386/386, PropertyTests 3/3, UnitTests 603/603, checkout finished clean (`CLEAN_STATUS=0`); output SHA-256 `207e2895a85c666e89e8f8f481049d830298225cab39c163b430d91bc8f62e7c`.
- **Local production scan on candidate:** 0 Works diagnostics, 8 handed-off Platform diagnostics, 0 run errors, 0 duplicates.
- **Publication gate (why held locally):** Publishing via the Works PR path requires the updated scanner to land on CiCd `main`, a normal hosted CiCd scan report covering exact Works `main` (`5d5b56e1`) at that scanner revision, and passing exact-base hosted `ci` + `platform-parity` on `5d5b56e1`.

## Platform owner handoff (8 remaining sites at `7eaa9eb8`)

Paths are relative to `references/Hexalith.Platform` at `7eaa9eb85d060b6d0d0c836a938ccb6e8795fa89`. Diagnostics omit the common `local-script discovery:` prefix.

| Platform site | Exact remaining diagnostic | Required Platform-owner change |
| --- | --- | --- |
| `eng/bound_builds.py:71` | `unresolved computed Python script invocation; unsafe or unresolved forwarding` | Replace `-c submodule.recurse=false` and `*map(str, arguments)` with direct safe literal Git subcommands/flags (`--no-recurse-submodules`, `--` terminator, explicit literal `checkout --detach ... --` / `clone` / `fetch`). |
| `eng/builds_tuple.py:93` | `unresolved subprocess positional/options expansion` | Inline the `git diff` argv list (instead of local `command = [...]`) and add `--end-of-options` before the computed `gitlink` revision. |
| `eng/retained_works_host.py:30` | `unsupported Git mode or unresolved Git options` | Add `--end-of-options` before the computed `commit + ":" + name` operand in `git show`. |
| `eng/verify_works_host.py:1044` | `unresolved computed Python script invocation; unsafe or unresolved forwarding` | Pass literal option terminator / non-computed tree-ish or keep `BUILD_FILES` local/explicit in `git archive` so operands are statically provable. |
| `eng/prepare_builds_artifacts.py:122` | `unresolved computed Python script invocation` | Extracted `.dll` path under `args.output` is runtime-computed; qualify or restructure without launching an unproved computed `.dll` path from the scanned verifier closure. |
| `eng/works_toolchain.py:77` | `unresolved computed Python script invocation` | Invokes computed binary `[str(runtime), "--version"]`; replace with a statically provable check or move outside the scanned closure. |
| `eng/isolated_daprd.py:50` | `unsupported reflective use of a process/import API: os.execv` | References `os.execv` as a default argument; isolate/replace outside the fail-closed `os.exec*` surface. |
| `eng/works_verifier_command.py:87` | `unresolved forwarded wrapper argv: the wrapper changes or passes on its parameter` | Cross-module process-group wrapper (`run_owned`) has no local callers and escapes `command` into `CompletedProcess`; inline or provide a statically provable boundary for its callers in `verify_works_host.py`. |

## Open prerequisites before Story 13 `done` closeout

1. **CiCd:** Publish the scanner update on CiCd `main` and collect a normal hosted scan report on exact Works `main`.
2. **Platform owners:** Resolve the 8 handed-off Platform sites above and pin the resulting Platform commit in Works `main`.
3. **Works (module-agent PR):** Push/merge the held `configparser` candidate (`ba908c0b`) once exact-base hosted scan and hosted CI (`ci` + `platform-parity`) satisfy the publication gate.
4. **Maintainer (AD-21 Zot):** Legacy Zot cleanup remains open (per 2026-11-28 Option A, maintainer-profile readbacks were skipped). Qualify scoped replacements for EventStore, Memories, Parties and Tenants, confirm continuity, retire the shared legacy Zot key, and verify loss of legacy Works write access before final acceptance Nightly (`tools/nightly_acceptance.py --run <run-id> --module Hexalith.Works` exit 0).
