# Cross-module duplicate scan

`tools/scan.py` runs in nightly after publication and before the Builds bump.
It reports generic custom-action code copied between modules so that a later
change can move that code into Builds. The scan makes no module or Builds edits.
Any cross-module finding or incomplete scan makes the job fail. Bump and
keepalive remain eligible after this ordinary failure, and nightly stays red.
Cancellation and the manual `qualify-bump` mode skip production scanning.

## Sources and scope

The registry is the committed `setup/*.yml` tree at the controller's CiCd
revision, capped at 17 modules. Invalid names, case collisions, symlinks and a
Builds registration fail. Registration includes modules awaiting adoption;
`delivered/*`, enabled hooks and local submodule checkouts do not determine scope.
Builds and unregistered repositories are never scanned.

Each module is fetched anonymously from its fixed GitHub `main` origin into a
private Git object store. Reports record the full canonical commit SHA. The
controller reads tracked regular blobs without checking out or executing module
code, applying filters, running Git hooks or initializing submodules. A source
blob is capped at 2 MiB; a module selects at most 2,000 files and 32 MiB; aggregate
staging is capped at 128 MiB, reports at 16 MiB and findings at 1,000. Fetch, parsing, discovery, unsafe
path, symlink, gitlink and capacity failures are explicit. A failed module cannot
prevent healthy siblings from contributing files and findings.

Supported YAML, shell, PowerShell and Python files beneath
`.github/actions/**` are initial sources, including dormant action directories.
The selected extensions are `.yml`, `.yaml`, `.sh`, `.bash`, `.ps1`, `.psm1` and
`.py`. Literal local calls are followed recursively, including local Python
imports and package initialization. A called extensionless script, or an action
source with a supported shell/Python shebang, is also included. Static discovery covers:

- Local composite `uses:` calls, literal `working-directory`, and literal Bash/sh `cd`.
- Workspace and action path expressions, their usual environment-variable
  forms, and PowerShell `$PSScriptRoot` paths.
- Direct script invocations, `bash`/`sh`, `pwsh`/`powershell`, shell `source` and
  dot sourcing, plus literal interpreter `-c` or `-Command` strings. Literal
  calls in `while`, `until` and `elif` conditions are included. PowerShell
  `Import-Module` accepts a literal local module directly or through `-Name`.
- Python file calls, `python -m package.module`, static `import`/`from` imports,
  namespace packages, package initializers and executable `__main__.py` files,
  and literal `subprocess`, `os.system` and `runpy` calls. File invocations retain
  their original script import root through recursive imports; `-m`, `-c` and
  inline Python action shells start from the known working directory.
- A literal subprocess `cwd` resolves relative to the invoking process's known
  working directory and is inherited by the child script's discovery. `None`
  retains that directory. Dynamic working directories, unsafe directory paths,
  alternate executable overrides and expanded/positional subprocess options
  that could change resolution fail with a source diagnostic. Computed `env`
  overrides and overrides of `PYTHONPATH`, `PYTHONHOME`, `PYTHONSAFEPATH` or
  `PATH` also fail coverage explicitly.
- Static subprocess, importlib and runpy aliases are followed inside functions
  and other scopes. Reused alias names retain all recognized possibilities.
  Python search-path mutations (`sys.path`, its aliases, import hooks and
  `site.addsitedir`) and process working-directory mutations fail coverage
  explicitly because their execution order is outside this static model.
- `env`/`exec`/`command` wrappers without options and literal `uv run` script
  targets. Wrapper option forms and uv `--directory`/`-C` fail coverage.

Command substitutions, shell functions/compound blocks, subshells, PowerShell
script blocks and `Start-Process` are explicit coverage failures. Directory
stack/location commands (`pushd`, `popd`, `Set-Location` and their supported
spellings) also fail. A sourced script that changes the caller's directory
fails coverage instead of letting later calls use a guessed directory. Quoted
ordinary data arguments remain data, including text that resembles these forms.

A path passed only as data is not a script call.
Repository configuration is never a detector input: `.jscpd*`, `.gitignore`,
`.ignore` and source suppression directives cannot waive detection.

Static discovery cannot resolve an arbitrary computed script path. A local call
with a missing, unsafe, unsupported or unresolved target is a failed coverage
diagnostic at the originating action or script. Make the target statically
identifiable or extend the central discovery implementation and its fixtures;
do not hide it through a module-specific exclusion. The scanner does not prove
that differently written implementations share no logic.

An empty registry succeeds with an explicit zero scope. A registered repository
with no custom-action sources also succeeds with zero files after recording its
live revision. Neither case means a failed fetch or unresolved call was clean.

## Detector and reports

CiCd owns `.jscpd.json` and `tools/jscpd/package{,-lock}.json`. The exact detector
version is **jscpd 5.4.3**, including package integrity pins. Installation uses
`npm ci --ignore-scripts`, then `npm audit signatures`, and checks the actual
version before scanning. Installation, signature, version, detector and output
validation failures are scan failures. The locked Python entry point requires
Python 3.12 or later. Dependency installation, module object stores, selected
source copies and raw detector output live in private disposable scratch.

The committed policy is weak mode, **10 lines / 50 tokens**, with the `yaml`,
`bash`, `powershell` and `python` formats, one root per module, `skipLocal`,
absolute report paths and Git ignores disabled. The wrapper authenticates every
reported endpoint against its own selected-file manifest and the original line
range. It gates only fragments involving distinct modules, independently of
jscpd's percentages. Same-module repetition alone passes. Unsupported,
incomplete or malformed reports and paths outside the selected roots fail.

The durable output directory contains:

- `report.json`: schema `hexalith.duplicate-scan.v1`, `result` (`pass` or `fail`),
  detector and policy observations, top-level errors, module names, full source
  revisions, selected original paths and per-module errors, and findings with
  format, lines, tokens, fragment and both original module/path/line endpoints.
- `summary.md`: the readable verdict, source coverage, diagnostics and copied
  fragments with the original locations of code to move into Builds.

The nightly job seeds both files before checkout and always uploads the directory
as `hexalith-nightly-scan-<attempt>`, retained for 90 days. It also preserves the
Markdown in the Actions summary. An unavailable controller or tooling leaves the
failed seed in place. Reports contain no scan credentials. Selected scope and
findings are deterministic for unchanged source revisions and policy; observation
metadata and future live main revisions may differ.

For a local scan, retain outputs outside disposable scratch:

```sh
SCAN_DIRECTORY="$PWD/../cicd-duplicate-scan-observations" run-with-temp uv run --locked tools/scan.py
```

Use Node 24 and Python 3.12 or later. Run from a checkout containing the committed
policy and registry. The production registry is intentionally empty until
onboarding; local synthetic registrations belong in temporary test repositories.

## Calibration and retuning

The retained [detector investigation](../_bmad-output/implementation-artifacts/story-9-detector-investigation.md)
records actual pinned-detector runs on 2026-11-15. Weak-mode exact-copy corpora
gave these measurements:

| Format | Substantial copied corpus | Measured tokens | At 10 lines / 100 tokens |
| --- | --- | --- | --- |
| Python | 18 print statements | 144 | Detected |
| Bash | 18 printf statements | 72 | Missed |
| PowerShell | 18 Write-Output statements | 72 | Missed |
| YAML | 12 two-line named steps | 180 | Detected |

The 50-token floor preserves the substantial shell and PowerShell blocks; the
10-line floor removes short scaffolding. Detector fence behavior is empirical:
an exactly five-line Python block with 90 tokens produced no clone at a
five-line minimum. Test examples must exceed both floors comfortably instead of
assuming inclusive boundaries from option names.

The committed scanner fixtures additionally measured the final 10/50 policy
through the production controller and real Git snapshots: YAML 36 lines / 216
tokens, Bash 18 / 54, PowerShell 18 / 72, and Python 18 / 144 all failed with
actionable cross-module findings. Three-statement fragments in each format
passed; same-module copies passed. These calibration observations are printed
by the enabled `test_all_four_languages_use_actual_pinned_detector` test and
reproduced by the commands below on Python 3.12 and the current interpreter.

The anonymous live-source measurements were:

| Module | Captured full main revision | Tracked action files | Optional broader Python tooling diagnostic |
| --- | --- | --- | --- |
| Hexalith.Memories | `2c2e9b58990638ededf22e8e67ff5c12de75b434` | 0 | 75 files |
| Hexalith.Tenants | `d89f234c4f020373aaabe0e3699ecdb5097b1079` | 0 | 22 files |

Their production action scope was empty. A separate diagnostic over all 97 Python
tooling files found zero cross-module copies at weak-mode 5/50 and 10/100. Those
files were outside production scope and are not added merely to manufacture
noise. These observations do not establish future noise rates for nonempty
action corpora and justify no module or language exclusions.

To retune, retain full live source identities and scope counts, run the real
pinned detector against substantial and short boilerplate examples in all four
formats, and compare findings before changing the central policy. Classify
false positives by the copied code and line ranges, then rerun the same corpus
with the candidate thresholds. Commit the measured tradeoff and keep the
substantial-clone, same-module, suppression and zero-scope checks enabled:

```sh
run-with-temp uv run --locked --script tools/tests/test_scan.py -v
run-with-temp uv run --locked --script --python 3.12 tools/tests/test_scan.py -v
run-with-temp uv run --locked --script tools/tests/test_nightly_workflow.py -v
```

Save useful results and logs outside the wrapper's temporary directory. No test
may silently skip detector integration. Moving shared code into Builds and
deleting module copies is a separate authorized change after inspecting the
reported fragments.
