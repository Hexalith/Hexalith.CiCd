# Story 9 detector investigation

Date: 2026-11-15. Read-only external investigation; all package installations,
Git clones and generated scan corpora ran beneath `run-with-temp`'s private
workspace and finished before cleanup. No module source was executed.

## Confirmed tool interface

Actual npm metadata and installed execution verified `jscpd@5.4.3`. This is a
Rust engine distributed through the npm wrapper and optional platform packages;
`npm install --ignore-scripts --save-exact jscpd@5.4.3` works without an install
script. `npm audit signatures` verified registry signatures and attestations
for the two installed packages. Lock the exact version and integrity through a
committed npm lockfile, and use `npm ci --ignore-scripts` for production.

Actual `--list` includes `yaml`, `bash`, `powershell`, and `python`. The CLI
accepts multiple path roots, explicit `--config`, `--skip-local`,
`--no-gitignore`, `--absolute`, `--reporters json`, and `--output`.
The JSON filename is `jscpd-report.json`. Verified shape:

```json
{
  "duplicates": [{
    "format": "python",
    "fragment": "source fragment",
    "lines": 14,
    "tokens": 112,
    "kind": "exact",
    "isNew": false,
    "firstFile": {
      "name": "/absolute/module/file.py",
      "start": 1,
      "end": 14,
      "startLoc": {"line": 1, "column": 0, "position": 0},
      "endLoc": {"line": 14, "column": 39, "position": 541}
    },
    "secondFile": {"name": "/absolute/other-module/file.py", "start": 1, "end": 14}
  }],
  "statistics": {"detectionDate": "timestamp", "formats": {}, "total": {}}
}
```

The actual second-file object has the same location fields as the first.
Without a threshold/exit-code option, the process exits zero even with clones;
the controller should decide failure from authenticated cross-module paths.

One supplied root per module plus `skipLocal: true` excludes duplicates inside
that module. A fixture with identical `A/a.py`, `A/b.py`, and `B/c.py` reported
one A/B pair; scanning A alone reported zero. Independently validate report
paths against the known materialized files/module roots.

## Threshold evidence

Actual weak-mode exact-copy fixtures:

| Language | Block | Tokens | Default 5 lines / 50 tokens | 10 lines / 100 tokens |
| --- | --- | --- | --- | --- |
| Python | 18 print statements | 144 | one clone | one clone |
| Bash | 18 printf statements | 72 | one clone | zero; files below token floor |
| PowerShell | 18 Write-Output statements | 72 | one clone | zero; files below token floor |
| YAML | 12 two-line named steps | 180 | one clone | one clone |

Raising the token floor to 100 loses ordinary shell and PowerShell fragments.
A starting policy of weak mode, 10 lines and 50 tokens preserves those blocks
and filters shorter scaffolding. Boundary semantics merit an executable fixture:
an exactly five-line Python block with 90 tokens was scanned but yielded no clone
at `minLines: 5`, so do not infer the fence behavior from the option name alone.
Substantive tests should exceed both floors comfortably.

## Live Python tooling diagnostic

Anonymous shallow live-main reads captured:

| Repository | Full main revision | Tracked action files | Diagnostic Python files under tests/tooling and tests/scripts |
| --- | --- | --- | --- |
| Hexalith.Memories | `2c2e9b58990638ededf22e8e67ff5c12de75b434` | 0 | 75 |
| Hexalith.Tenants | `d89f234c4f020373aaabe0e3699ecdb5097b1079` | 0 | 22 |

Neither repository currently exposes a hook-reachable custom-action corpus.
This makes its production-scope result vacuous, not evidence that an arbitrary
threshold is tuned. A separate broader Python tooling diagnostic (97 source
files, explicitly outside production scope) reported zero exact cross-module
clones at both 5/50 and 10/100 in weak mode. The previously anticipated tooling
noise therefore was not reproduced at these captured revisions; do not add
module-specific ignores or scan unrelated tooling in response to stale counts.

## Scope and suppression pitfalls

- Materialize tracked regular source blobs selected from live main; do not
  checkout or execute module scripts. Exclude symlinks/gitlinks and fail if a
  referenced source is outside the module or missing.
- All `.github/actions/**` sources include dormant actions. Traverse literal
  local action calls and supported local script calls recursively. Python AST
  imports/from-imports can resolve tracked repository-local modules and package
  `__init__.py` files. Do not expand an unresolved computed target into success;
  fail with the action/script and expression requiring clarification.
- Common literal contexts include repo-relative commands, action-path and
  workspace-path expressions, fixed working-directory, Python relative/local
  imports, `python -m package.module`, shell source calls, and PowerShell
  `$PSScriptRoot` wrappers. Paths used as data arguments are not script calls.
- `noGitignore: true` disables Git ignores, but `.ignore` is separately honored.
  Materializing selected source alone prevents module-owned ignore/config files
  from influencing enumeration. Always pass the CiCd config explicitly.
- jscpd honors `jscpd:ignore-start` / `jscpd:ignore-end` in every mode. Reject
  these markers or neutralize them with position-preserving transformation if
  module source must never suppress central detection.
- The global percentage threshold is the wrong failure decision: the required
  policy is any clone across two distinct modules, with module/path/range/code
  in the report. Detector/process/report failures must fail closed.

## Primary references

- [jscpd 5.4.3 CLI reference](https://jscpd.dev/reference/cli)
- [Committed-config precedence, modes and ignores](https://jscpd.dev/reference/config-file)
- [JSON reporter contract](https://jscpd.dev/reference/reporters/json)
- [Monorepo root isolation](https://jscpd.dev/guides/monorepos)
- npm registry metadata for `jscpd@5.4.3`, queried directly with `npm view`;
  CLI/report behavior above was independently exercised against that release.

## Final controller calibration

The implemented `tools/tests/test_scan.py` creates committed local Git remotes,
passes their current full main revisions through the production controller,
installs the committed integrity-pinned detector with scripts disabled, verifies
npm signatures, and exercises the final weak-mode 10-line / 50-token policy.
The actual reported substantial-copy fragments were:

| Format | Reported lines | Reported tokens | Final policy |
| --- | --- | --- | --- |
| YAML | 36 | 216 | Detected |
| Bash | 18 | 54 | Detected |
| PowerShell | 18 | 72 | Detected |
| Python | 18 | 144 | Detected |

Each format's three-statement boilerplate corpus passed, as did repeated
substantial fragments confined to one module. Three-module copies implicated
all three modules. Module config, ignore files and source suppression directives
did not hide the copies. The Bash fixture uses `printf '%s\\n' 'message'`; its
54-token count is a different corpus from the earlier 72-token investigation.

Reproduction (all matrix cases enabled; installation, snapshots and raw outputs
remain under the wrapper's private TMPDIR):

```sh
run-with-temp uv run --locked --script tools/tests/test_scan.py -v
run-with-temp uv run --locked --script --python 3.12 tools/tests/test_scan.py -v
```

Useful local verification logs are retained alongside this document as
`story-9-scan-tests.log` and `story-9-scan-tests-python312.log` (Git-ignored log
files), outside disposable scratch. This synthetic calibration does not change
the empty live Memories/Tenants action scope or the separate 97-file diagnostic.
