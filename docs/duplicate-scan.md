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

An empty registry succeeds with an explicit zero scope. A registered repository
with no custom-action sources also succeeds with zero files after recording its
live revision. Neither case means a failed fetch or unresolved call was clean.
Repository configuration is never a detector input: `.jscpd*`, `.gitignore`,
`.ignore` and source suppression directives cannot waive detection.

## Discovery coverage model

Initial sources are the YAML, shell, PowerShell and Python files beneath
`.github/actions/**`, including dormant action directories. The selected
extensions are `.yml`, `.yaml`, `.sh`, `.bash`, `.ps1`, `.psm1` and `.py`. An
extensionless file with a shebang is selected too, and fails as an unsupported
language unless the shebang names a shell, PowerShell or Python. A dormant file's
action context, which `$GITHUB_ACTION_PATH` names, is its nearest ancestor
directory holding `action.yml` or `action.yaml`. Discovery reads every reachable
source as data and never executes it. Recognized calls refine resolution only.
Two fail-safe rules decide coverage: literal references are included, and
unmodeled indirection fails.

### Recognized calls refine resolution

Recognized forms supply the exact working directory, import roots and language:

- Each composite step is discovered independently, and its diagnostics name the
  step's line. A local `uses:` names exactly one `action.yml`/`action.yaml` under
  `.github/actions/`; any other `uses:` must pin a full commit SHA. Literal
  `working-directory` and literal Bash `cd` set the working directory.
- Workspace and action path expressions, their environment-variable forms
  (only at a variable-name boundary) and PowerShell `$PSScriptRoot`.
- Direct script paths; `bash`, `sh`, `dash`, `zsh`, `ksh`, `pwsh` and
  `powershell`; `source` and dot sourcing; literal `-c` and `-Command` strings;
  PowerShell `Import-Module` (directly or through `-Name`) and `using module`.
  Interpreter options are read positionally, so later words are script
  arguments. Versioned and `.exe` interpreter spellings are recognized.
- The `env`, `exec`, `command`, `builtin`, `coproc`, `time`, `nohup`, `nice`,
  `sudo`, `doas`, `setsid`, `stdbuf`, `ionice`, `unbuffer` and `xargs` wrappers,
  plus `timeout DURATION`, `flock FILE` and `chrt PRIORITY`, also when called by
  absolute path. `command -v` and `command -V` are non-executing probes. Leading
  list and block words (`then`, `do`, `else`, `{`, `}`, `try`, `catch`,
  `finally` and similar), redirections and `NAME=value` or `NAME+=value` prefixes
  are skipped.
- `uv run` with every known option value consumed, where `-m`/`--module` means
  `python -m` and `--script`/`--gui-script` runs the target as Python, and the
  child command of `poetry`, `pipenv`, `pdm` and `hatch run`.
- Literal `eval`/`Invoke-Expression` text, `trap` handlers (including after
  `--`) and `find -exec`/`-ok` commands.
- Python file calls, `python -m` (a package's `__main__.py`), static
  `import`/`from` imports, namespace packages and every enclosing `__init__.py`.
  Literal `subprocess`, `os.system`, `os.popen`, `runpy`, `importlib.import_module`
  and `__import__` calls are followed too. So are static name aliases of these
  APIs, and `sys.executable` (or an alias of it) as argv[0]. A literal subprocess
  `cwd` applies to its child. File invocations keep the script's import root;
  `-m`, `-c` and inline Python action shells start from the working directory.

### Rule 1: literal references are included

Every literal in a reachable source counts: a shell word after quote removal, a
Python string constant (including list and tuple elements and the words inside
it), or a scalar in an action file. It is a reference when it names a tracked
regular shell, PowerShell or Python script, by suffix or as an extensionless file
with a supported shebang. The reference is included and traversed whatever
consumes it: any command, wrapper, runner, block, pipeline, redirection, heredoc
body or API. For example, `cat scripts/tool.py` and `echo "see scripts/x.sh"`
include those scripts.

References resolve against every candidate base:

- the workspace root;
- the owning action directory;
- the referencing file's directory;
- every literal working directory that the source establishes, before and after
  each change, so a conditional `cd` keeps both directories.

Every match is included, and over-inclusion is acceptable. A literal never pulls
in YAML outside `.github/actions`, and a literal that names nothing is data.

Module names follow the same rule. In any literal sequence (a line's shell words,
a heredoc body line, a Python string, a list, tuple or set, or a call's
arguments), the operand of `-m` or `--module` names a module. So does every
module that the Python code in a `-c` operand imports, including through
`importlib.import_module`, `__import__` or `runpy.run_module`. A word holding
whitespace is tokenized again, so command strings and nested `bash -c` or
`pwsh -Command` text count too. Each module resolves from every base as an
import root; its file, its package initializer and `__main__.py`, and every
enclosing `__init__.py` are included. So `xvfb-run python -m tool`,
`Start-Job { python -m tool }` and
`sys.modules['subprocess'].run(['python', '-m', 'tool'])` include a local
`tool.py` even though the consumer is unrecognized.

From an execution position (a command word, interpreter operand, sourced path or
`runpy.run_path` target), a literal is resolved precisely first. When that exact
target is not tracked, every base is tried, and the literal fails coverage only
when it resolves against none of them. A precise path that is unsafe, escapes the
module or crosses a symlink, blob or gitlink still fails. A tracked script in
another supported language also fails, for example `bash x.py`, `python x.sh`,
`pwsh -File x.sh`, `uv run --script x.sh`, Bash `source x.py` or `. x.ps1`, or
`bash tool` when `tool` has a Python shebang. Sourcing runs the target in the
current shell's language, and a directly executed script whose shebang names a
different supported language than its suffix fails as ambiguous. A `node`,
`nodejs`, `deno`, `bun`, `ruby`, `perl` or `php` call of a tracked local script
also fails, as an unsupported language.

Python imports resolve against every candidate root: the invocation roots, the
importing file's directory, the working directory and the workspace root. Every
match is included. A required `python -m` module fails as missing only when its
top-level package exists locally; otherwise, as with `pip`, it is an installed
tool. A `from module import name` of a non-local module never selects a local
file named `name`.

### Rule 2: unmodeled indirection fails

These fail coverage with a diagnostic naming the source file and line:

- A computed value in an execution position: a command word, interpreter
  operand, sourced path, import or process-API target, or working directory.
  The structural forms are command substitution (`$(...)` and backticks),
  subshells and other parenthesized syntax, and shell function definitions. So
  are brace groups that start a list, PowerShell script blocks (`& { ... }`),
  `pushd`/`popd`/`Set-Location` and their aliases, and PowerShell `cd`. Also
  covered: a sourced or evaluated script that changes the caller's directory,
  `find -execdir`/`-okdir` and `-exec {}`, `Start-Process` and `Invoke-Command`.
  Options that redirect execution fail as well: `pwsh -WorkingDirectory`,
  `-EncodedCommand` and `-CommandWithArgs`, `uv --directory`/`-C`, unknown `uv`
  options, wrapper options and task-runner options.
- An interpreter fed from stdin or a heredoc, such as `bash <<EOF`,
  `python - <<'EOF'`, `pwsh -Command -`, `bash -s`, `python -` or
  `cat x.py | python`.
- `PYTHONPATH`, `PYTHONHOME`, `PYTHONSAFEPATH`, `PYTHONUSERBASE` or `UV_ENV_FILE`,
  or the name-based lookup paths `PSModulePath` and `CDPATH`, set by any means:
  - a shell assignment, including `+=`, or `export`/`declare`;
  - a composite step `env` entry, or a non-mapping step `env`;
  - PowerShell `$env:` or `Set-Item env:`;
  - Python `os.environ` or `os.environb` (a computed or resolution key, or
    replacing or merging into the mapping with `=` or `|=`), `os.putenv` or a
    subprocess `env`;
  - an env file through `uv --env-file` or python-dotenv's `load_dotenv`;
  - a `$GITHUB_ENV` write.

  A computed environment name in `export`/`declare` fails too.
- A `PATH` value, or a `$GITHUB_PATH` write, that adds a relative, workspace or
  action-path directory, or any computed component other than `$PATH` and
  `$HOME`. Absolute literal directories and `$HOME/...` pass. Python `PATH`
  writes and subprocess `PATH` overrides always fail.
- A `$GITHUB_ENV` write with a computed key, meaning that line has no literal
  `NAME=` or `NAME<<`. Python code that names `GITHUB_ENV` or `GITHUB_PATH` fails
  too.
- Reflective use of a process or import API. That means storing it in an
  attribute, a class body, a tuple or a container; passing it as an argument;
  using it as a default, a return value or a walrus target; or fetching it with
  `getattr`. A plain name alias is followed instead, and type annotations,
  comparisons and `isinstance`-style inspection are not uses. The following
  fail too:
  - `eval`, `exec`, `compile` and the file-location import loaders;
  - `os.exec*`, `os.spawn*`, `os.posix_spawn*`, `asyncio.create_subprocess_*` and
    `pty.spawn`;
  - star imports of process/import modules, and `functools.partial` of one of
    these APIs;
  - Python search-path mutations (`sys.path`, its aliases, import hooks and
    `site.addsitedir`) and working-directory mutations (`os.chdir`,
    `contextlib.chdir`).
- A task runner whose recipes are tracked module files:
  - `make`/`gmake` with a tracked Makefile;
  - `just`, `task`, `invoke`, `nox`, `tox`, `poe`, `rake` or `pre-commit` with
    its tracked recipe file, also as `python -m tox` or `python -m pre_commit`;
  - `pytest`, `py.test`, `python -m pytest`, `python -m unittest` or
    `python -m nose2` when the module tracks `conftest.py` or a file named
    `test*.py` or `*_test.py`;
  - `npm`, `pnpm`, `yarn` or `bun` with a tracked `package.json`, unless
    `--ignore-scripts` is given or the subcommand runs no scripts;
  - `uv`, `poetry`, `pipenv`, `pdm` or `hatch run` of a script name defined in a
    tracked `pyproject.toml`, `Pipfile` or `hatch.toml`.

  An explicit recipe file or directory option fails as well.

### Lines, comments and data

Shell and PowerShell sources split only on LF, and a trailing CR is dropped.
Other separators, such as U+2028, form feed or a lone CR, stay inside the line.
The continuation character is a backslash in shell and a backtick in PowerShell,
and nothing else. A logical line keeps its first physical line number in
diagnostics. A comment starts only at a word boundary, so `$#` and `a#b` are
words. PowerShell `<# ... #>` comments are removed wherever they occur, without
changing line numbers. A UTF-8 byte-order mark is ignored for parsing.

Heredoc bodies fed to any command other than an interpreter are data, and so are
PowerShell here-string bodies. They are scanned for literal references and never
parsed as commands. Quoted ordinary data stays data, including text that
resembles the failing forms above.

### Conservative failures and limits

Some ordinary constructs that call no local script still fail, because their
structure is unmodeled: `$(date)`, parenthesized `case` patterns, PowerShell
variable assignments, and PowerShell `if (...)` or `foreach (...)` blocks. Make
such a call statically identifiable, or extend central discovery and its
fixtures before onboarding a module whose actions rely on them. Never hide a
call through a module-specific exclusion. The scanner does not prove that
differently written implementations share no logic.

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
  fragments with the original locations of code to move into Builds. Each
  fragment is a top-level fenced block longer than any backtick run it contains,
  so module text stays inert Markdown. Fragment lines follow the detector's
  LF-only line numbering.

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
