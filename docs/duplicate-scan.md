# Cross-module duplicate scan

`scan.yml` runs `tools/scan.py` daily at **03:07 UTC**. To run it on demand,
open **Cross-module duplicate scan** in CiCd Actions and choose **Run workflow**
on `main`. The job has a 55-minute limit and a Contents-read job token. The
controller and policy are checked out at the triggering CiCd commit. The scan
step is capped at 42 minutes to leave time for the summary and upload.
The controller scans registered public modules anonymously and reports
custom-action code copied between modules. A cross-module finding or incomplete
coverage fails the scan run and names the affected source. Nightly releases
and the Builds bump have their own verdicts. Nightly keepalive enables
`scan.yml` alongside the other scheduled workflows.

## Sources and scope

The registry is the committed [`setup/*.yml` tree](../setup/) at the controller's CiCd
revision, capped at 17 modules. Invalid names, case collisions, symlinks and a
Builds registration fail. Registration includes modules awaiting adoption;
`delivered/*`, enabled hooks and local submodule checkouts do not determine scope.
Every scan root is a registered module.

Each module is fetched anonymously from its fixed GitHub `main` origin into a
private Git object store. Reports record the full canonical commit SHA. The
controller reads tracked regular blobs without checking out or executing module
code, applying filters, running Git hooks or initializing submodules. When a
literal execution path enters a direct submodule, its path must appear in the
controller's committed module setup and have one matching committed
`.gitmodules` declaration with the official origin. The controller fetches the
gitlink's exact commit into a separate private object store, follows reachable
sources under the dependency path, and records its revision in the module's
`pinnedSources` field. Nested gitlinks, symlinks and traversal through the
dependency path fail discovery.

A source blob is capped at 2 MiB; a module selects at most 2,000 files and 32 MiB; aggregate
staging is capped at 128 MiB, reports at 16 MiB and findings at 1,000. Fetch, parsing, discovery, unsafe
path, symlink, gitlink and capacity failures are explicit. A failed module cannot
prevent healthy siblings from contributing files and findings.

An empty registry succeeds with an explicit zero scope. A registered repository
with no custom-action sources also succeeds with zero files after recording its
live revision. Neither case means a failed fetch or unresolved call was clean.
Repository configuration is never a detector input: `.jscpd*`, `.gitignore`,
`.ignore` and source suppression directives cannot waive detection.

## Discovery coverage model

Initial sources are the YAML, shell, PowerShell, Python, JavaScript and TypeScript files beneath
`.github/actions/**`, including dormant action directories. The selected
extensions are `.yml`, `.yaml`, `.sh`, `.bash`, `.ps1`, `.psm1`, `.py`,
`.js`, `.mjs`, `.cjs`, `.ts`, `.mts` and `.cts`. An
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
  `working-directory` and literal Bash `cd` establish candidate working
  directories. Each later `cd` extends every preceding candidate, retaining
  both before/after contexts, including successive conditional changes.
- Workspace and action path expressions, their environment-variable forms
  (only at a variable-name boundary) and PowerShell `$PSScriptRoot`.
- Direct script paths; `bash`, `sh`, `dash`, `zsh`, `ksh`, `pwsh` and
  `powershell`; `source` and dot sourcing; literal `-c` and `-Command` strings;
  PowerShell `Import-Module` (directly or through `-Name`) and `using module`.
  Literal local modules in PowerShell `#requires -Modules` are traversed too.
  Literal attached parameter values such as `-Command:` retain their AST type.
  Interpreter options are read positionally, so later words are script
  arguments. Versioned and `.exe` interpreter spellings are recognized. A
  standalone Bash launcher can resolve a fixed Python script from
  `BASH_SOURCE[0]`. A bounded launcher that changes to an ancestor of its
  source directory before running a fixed Python script uses that directory
  for the child's working directory. A standalone Bash script can establish
  the same ancestor immediately after `set -euo pipefail` in a contiguous
  prologue that allocates a private scratch directory with `mktemp -d`,
  installs its cleanup trap, and changes directory.
- The `env`, `exec`, `command`, `builtin`, `coproc`, `time`, `nohup`, `nice`,
  `sudo`, `doas`, `setsid`, `stdbuf`, `ionice`, `unbuffer` and `xargs` wrappers,
  plus `timeout DURATION`, `flock FILE` and `chrt PRIORITY`, also when called by
  absolute path. GNU `timeout` accepts literal durations and the supported
  literal options `--signal=SIGNAL`, `--kill-after=DURATION`, `--foreground`,
  `--preserve-status` and `--verbose`. `command -v` and `command -V` are
  non-executing probes. The Linux `after-unit-tests` hook may run a literal
  Python script through the shared prepared virtual environment under a
  literal `timeout`. Discovery requires native preparation and the enabled
  hook in committed CI configuration, plus the matching official shared CI
  workflow at an immutable Builds v6 release from v6.2.0 onward. Action
  environment writes may not override `HEXALITH_CI_PYTHON`. Leading
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
  `python -m unittest discover` accepts an explicit literal start directory
  and a literal filename pattern. It includes every matching test source and
  package initializer below that directory, and fails for unsafe sources.
  A standalone Bash `python -` command on one line can read a closed, fully quoted heredoc.
  Its LF-delimited body is traversed as Python from every candidate working
  directory. Only literal words and quoted simple parameter expansions can
  follow the stdin marker.
  An early top-level Python import-path insertion can prove its source root
  from the imports, source-relative assignments and previously proved
  insertions that precede it.
- Python argv with a fixed `dotnet build`, `pack`, `restore`, `msbuild`, or
  `tool run NAME` prefix consumes project, output and property data at the
  compiled-language boundary. The executable, operation and tool name must be
  literal, with no argv expansion. Literal script references in these data
  operands still enter discovery. Computed executable, operation, shell,
  working-directory or resolution-environment changes remain failures.
  Bash calls to the same fixed build, pack, restore and msbuild operations
  also accept simple shell parameter expansion in the data operands.
  Bash `grep` accepts simple parameter expansion in its data operands and a
  literal trailing dollar in its pattern.
- Python subprocess argv using the standard Git executable can read metadata
  with literal `rev-parse`, `ls-files`, `ls-tree`, `status`, `cat-file`,
  `diff`, `show`, `archive` and `remote get-url` and supported literal flags.
  A computed `cwd` or `-C` operand is directory data. Computed paths after
  `--` are data. Modes with execution-sensitive options require proof that a
  computed operand cannot be treated as one of those options. Use
  `--end-of-options` before computed revisions in `diff` and `show`. A local
  `clone`, `fetch` or `checkout --detach` requires safe literal flags and
  `--`. Computed verbs, Git aliases, `-c`, `config`, `hook`, and
  `submodule foreach` fail. Literal tracked scripts remain in scope, including
  those under a proved literal working directory or `-C` path.
- Direct Python `*args` wrappers and finite literal tuple loops are expanded
  within fixed depth, argument and variant budgets. Aliased or replaced
  callables, reflective namespace changes, unknown callers and computed
  process options fail. Copied `os.environ` mappings permit only proved
  resolution-preserving mutations and cannot escape through aliases/callbacks.
  Git wrappers must meet the same rules at every call site. A constant tuple
  can supply literal operands. A conditional `**` mapping may supply only
  the subprocess `env` keyword, and the environment must preserve executable
  resolution in each branch. Git mode proof does not permit a shell,
  alternate executable, pre-execution callback or unresolved environment.

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
Selected children are traversed under every established working directory,
including when an earlier reference already selected that child. Selection does
not erase an additional invocation context. Traversal remains bounded at 8,000
distinct file/context combinations; exceeding that bound fails coverage.

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
`tool.py` across the precise and conservative discovery paths.
Ancestor initializers are included even when the exact imported namespace has
neither `__init__.py` nor `__main__.py`. Action input defaults and step `with`
scalars participate in literal reference discovery as well.

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
file named `name`. Every precise import and literal-module fallback checks the
leaf, each intermediate package-path component and all ancestor initializers.
Tracked symlinks and gitlinks fail as unsafe; an unsafe package directory or
initializer cannot disappear as a non-local import.

### Rule 2: unmodeled indirection fails

These fail coverage with a diagnostic naming the source file and line:

- A computed value in an execution position: a command word, interpreter
  operand, sourced path, import or process-API target, or working directory.
  The structural forms are command substitution (`$(...)` and backticks),
  Bash subshells and other parenthesized syntax, and Bash function definitions.
  PowerShell declarations, assignments, conditions and function bodies are
  parsed with PowerShell's AST parser; every nested command is inspected,
  including commands in assignment values and interpolated subexpressions.
  Computed PowerShell invocations, argument expressions, argument splatting,
  method calls, and pipeline-fed `Invoke-Expression` remain unsupported. So
  are brace groups that start a Bash list, PowerShell script blocks (`& { ... }`),
  `pushd`/`popd`/`Set-Location` and their aliases, and PowerShell `cd`. Also
  covered: a sourced or evaluated script that changes the caller's directory,
  `find -execdir`/`-okdir` and `-exec {}`, `Start-Process` and `Invoke-Command`.
  Options that redirect execution fail as well: `pwsh -WorkingDirectory`,
  `-EncodedCommand` and `-CommandWithArgs`, `uv --directory`/`-C`, unknown `uv`
  options, `uv --project` recipe-root selection, wrapper options and task-runner
  options. Bash `--rcfile` and `--init-file` startup sources fail explicitly.
  An interpreter behind an unknown consumer still establishes execution
  positions: `xvfb-run python "$TARGET"` fails. An unknown consumer also cannot
  certify a computed operand as nonexecuting data, so `xvfb-run "$COMMAND"`
  fails. Ordinary quoted data under recognized data commands such as `echo`
  and `printf` stays data. An execution-bearing inline
  literal over the 4,096-character discovery limit fails visibly, including
  `-c` programs in literal sequences behind unrecognized Python consumers.
- An interpreter fed from stdin or a heredoc outside the closed, quoted Python
  form, such as `bash <<EOF`, `python - <<EOF`, `pwsh -Command -`,
  `bash -s`, `python -` or `cat x.py | python`.
- `PYTHONPATH`, `PYTHONHOME`, `PYTHONSAFEPATH`, `PYTHONUSERBASE` or `UV_ENV_FILE`,
  or the name-based lookup paths `PSModulePath` and `CDPATH`, set by any means:
  - a shell assignment, including `+=`, or `export`/`declare`;
  - a composite step `env` entry, or a non-mapping step `env`;
  - PowerShell `$env:` (including compound assignments and increment/decrement)
    or `Set-Item env:`;
  - Python `os.environ` or `os.environb` (a computed or resolution key, or
    replacing or merging into the mapping with `=` or `|=`), `os.putenv` or a
    subprocess `env`;
  - an env file through `uv --env-file` or python-dotenv's `load_dotenv`;
  - a `$GITHUB_ENV` write.

  A computed environment name in `export`/`declare` fails too, as does shell
  `read` assigning a resolution-affecting or computed variable name, including
  indexed destinations such as `PATH[0]`.
- A `PATH` value, or a `$GITHUB_PATH` write, that adds a relative, workspace or
  action-path directory, or any computed component other than `$PATH` and
  `$HOME`. Absolute literal directories and `$HOME/...` pass. Python `PATH`
  writes and subprocess `PATH` overrides always fail. Path-file writes use the
  same bounded literal-producer checks as environment-file writes: only the
  actual destination is exempt, and every emitted path line is checked.
  Path-file records split on CRLF, lone CR and LF, matching the runner's path
  reader. Source line numbers and Linux environment-file parsing keep LF semantics.
  A word containing `GITHUB_PATH` cannot conceal computed emitted output.
- A `$GITHUB_ENV` write with a computed key or unmodeled computed emitted output.
  Only an exact understood redirection target is a destination. A word such as
  `$CONFIG$GITHUB_ENV` or `GITHUB_ENV$CONFIG` remains computed emitted output.
  Every output argument is checked: a harmless literal `MODE=fast` does not
  certify a second computed argument or a command's heredoc body. The scanner
  accepts literal `echo`/`Write-Output` writes and a bounded `printf` subset
  (`%s`, `%%`, and newline/tab/carriage-return/backslash format escapes). It
  validates the complete derived output. PowerShell `Write-Output` and its
  `echo` alias emit one line per argument; Bash `echo` joins its arguments.
  Other producers, `%b`, octal/hex
  escapes and unmodeled formatting fail; no module command runs to derive
  output. Fully understood harmless writes pass. Python code that names `GITHUB_ENV` or
  `GITHUB_PATH` fails too.
- Reflective use of a process or import API. That means storing it in an
  attribute, a class body, a tuple or a container; passing it as an argument;
  using it as a default, a return value or a walrus target; or fetching it with
  `getattr`. A plain name alias is followed instead, and type annotations,
  comparisons and `isinstance`-style inspection are not uses. The following
  fail too:
  - reflective `builtins`/`__builtins__` namespace access, such as
    `builtins.__dict__['__import__']`, and reflective use of a process/import
    namespace returned by `__import__` or `importlib.import_module`, such as
    `getattr(__import__('subprocess'), 'run')` or
    `builtins.__dict__.get('__import__')`. Direct supported calls through a
    literal imported namespace or `sys.modules['subprocess']` use the same
    operand validation as ordinary calls; computed targets still fail;
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
  - unmodeled `npm` execution forms, or `pnpm`, `yarn` or `bun` with a tracked
    `package.json`, unless the subcommand runs no scripts. Supported literal npm
    recipes are described below. `--ignore-scripts` disables lifecycle hooks for
    dependency installation, but never exempts explicitly named `run` scripts;
  - `uv`, `poetry`, `pipenv`, `pdm` or `hatch run` of a script name defined in a
    tracked `pyproject.toml`, `Pipfile` or `hatch.toml`, including installed
    module forms such as `python -m poetry run lint`;
  - other project operations with tracked project configuration, such as
    `uv build`, because they can execute a local build backend. The scanner
    also rejects `run` preparation when `pyproject.toml` declares a build system,
    including a standard backend executing tracked `setup.py`, even if the
    visible child is harmless. An actual uv
    `--no-project` or `--no-sync` option before the child disables that
    project preparation check; the child's arguments cannot do so. Explicit
    local dependency sources, such as `uv run --no-project --with .`, still
    require preparation and fail before those exemptions. Public-package
    `--with` operands remain supported. The scanner never imports or executes
    a backend.

  An explicit recipe file or directory option fails before its value can be
  mistaken for a safe subcommand. This includes leading selectors in module
  forms such as `python -m poetry --directory tools run lint`. Plain
  nonexecuting npm info/version/audit and runner version probes remain supported.

### Lines, comments and data

Shell and PowerShell sources split only on LF, and a trailing CR is dropped.
Other separators, such as U+2028, form feed or a lone CR, stay inside the line.
The continuation character is a backslash in shell and a backtick in PowerShell,
and nothing else. A logical line keeps its first physical line number in
diagnostics. A comment starts only at a word boundary, so `$#` and `a#b` are
words. PowerShell `<# ... #>` comments are removed wherever they occur outside
quoted strings, without changing line numbers. Quoted `<#` and `#>` are data.
A UTF-8 byte-order mark is ignored for parsing.

Heredoc bodies fed to any command other than an interpreter are scanned for
literal references and never parsed as commands. A heredoc writing an environment
file fails when its full output producer is unmodeled. An unquoted shell heredoc
additionally performs expansions: backslash-newline continuations are removed
before checking command substitutions and backticks, which fail coverage with
physical source positions. The complete delimiter word undergoes quote removal,
so `E'OF'` terminates at `EOF`; unsupported delimiter syntax fails visibly.
Quoting any part of the delimiter suppresses body expansion. PowerShell
double-quoted here-strings also expand, and their unmodeled subexpressions fail;
single-quoted here-strings remain literal-reference data. Ordinary quoted data
stays data, including text that resembles the failing forms above.

### Conservative failures and limits

Some ordinary constructs that call no local script still fail, because their
structure is unmodeled: Bash `$(date)` and parenthesized `case` patterns,
PowerShell method calls, and computed operands of unknown commands. PowerShell
`param(...)`, variable assignments, arrays, hashtables, functions, `if (...)`
and `foreach (...)` are parsed as syntax rather than executable command names.
Direct, literal `&` and dot-source calls inside those constructs are followed.
Property/index assignment targets and writes affecting PowerShell command
resolution, including alias mutation, remain unsupported. Make
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
`bash`, `powershell`, `python`, `javascript` and `typescript` formats, one root per module, `skipLocal`,
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

The scan job seeds both files before checkout, writes the Markdown to the
Actions summary and attempts to upload the two files even after an ordinary
failure. Cancellation or runner loss can interrupt finalization. Successful
uploads are retained for 90 days as `hexalith-nightly-scan-<attempt>`. An
unavailable controller or tooling leaves the failed seed in place. Reports
contain no scan credentials. Selected scope and findings are deterministic for
unchanged source revisions and policy. Observation metadata and future live
main revisions may differ.

For a module's release acceptance, the read-only acceptance tool checks the
scan row for its exact dispatch commit. It uses the same attempt's artifact for
historical Nightly runs with a scan job. To qualify a newer Nightly on demand,
start the scan after Nightly starts while the live module heads still match its
dispatch SHAs. The reader evaluates a single listing of at most 100 completed
independent scans on `main` since Nightly started. It uses the current attempt
of the first qualifying run, ordered by creation time and run ID, with a row
for the exact dispatch commit. A failed row or duplicate involving the module
still fails acceptance if a later scan passes. Record the deciding scan run and
attempt, artifact name, ID and SHA-256 digest, and dispatch SHA alongside the
compact receipt. See [Testing on demand](nightly.md#testing-on-demand).

For a standalone local scan, use an existing checkout and toolchain and retain
outputs outside disposable scratch. `UV_NO_CACHE=1` puts uv's temporary cache and
environments under the wrapper's scratch and propagates to child uv processes:

```sh
SCAN_DIRECTORY="$PWD/../cicd-duplicate-scan-observations" run-with-temp env UV_NO_CACHE=1 uv run --locked --script --python 3.12 tools/scan.py
```

Use the [Linux bootstrap](../README.md#linux-maintainer-quickstart) for uv 0.13.7,
Python 3.12 and adjacent script locks. Use Node 24 with npm, plus PowerShell 7
(tested: 7.6.2; `pwsh`) when PowerShell
sources are reachable. A fixed parser helper reads source on stdin through
the native parser's `ModuleAnalysis` mode, avoiding host module lookup and type
resolution. It never evaluates, imports or dot-sources module text. The internal
analysis API must be present; incompatible PowerShell versions fail explicitly.
An unavailable parser, timeout, parse error or malformed parser output fails
coverage explicitly. Profiles are disabled. Run from a checkout containing the committed
policy and live [registrations](../setup/), including those awaiting adoption;
local synthetic registrations belong in temporary test repositories. npm needs
HTTPS access to `https://registry.npmjs.org` for the integrity-locked jscpd 5.4.3
and TypeScript 6.0.3 packages
and access to signature/provenance verification services. `npm audit signatures`
is mandatory: a refusal or failed audit fails the scan, including zero-scope
scans. Production scans additionally need anonymous GitHub Git access.

The focused integration case installs and verifies the real pinned detector,
then measures substantial copied examples in all six configured
formats. It requires compatible PowerShell 7 with the native `ModuleAnalysis`
API (tested: 7.6.2) even when no live registered module has PowerShell sources;
its fixtures include that format. For a fresh bootstrap, insert the focused
command below inside `BOOTSTRAP`, after the offline suite and before the final
assertions and cleanup. Omit its `run-with-temp` prefix because the outer wrapper
already owns scratch; the bootstrap deletes its checkout and uv on exit.
Standalone use requires an existing parent checkout and toolchain. Run from the
parent root with Node 24/npm and `pwsh` on `PATH`:

```sh
run-with-temp env UV_NO_CACHE=1 uv run --locked --script --python 3.12 tools/tests/test_scan.py \
  ScanTests.test_all_six_languages_use_actual_pinned_detector -v
```

This case uses local synthetic Git sources rather than live module origins.
Registry or signature access failures leave detector integration unproven;
offline controller success does not qualify it.

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

The 2026-11-15 scanner fixtures additionally measured the final 10/50 policy
through the production controller and real Git snapshots: YAML 36 lines / 216
tokens, Bash 18 / 54, PowerShell 18 / 72, and Python 18 / 144 all failed with
actionable cross-module findings. Three-statement fragments in each format
passed; same-module copies passed. These are historical four-format observations.
The current `ScanTests.test_all_six_languages_use_actual_pinned_detector` case
also covers JavaScript and TypeScript and prints its measured calibration
results; the focused command above reproduces the current case.

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
pinned detector against substantial and short boilerplate examples in all six
formats, and compare findings before changing the central policy. Classify
false positives by the copied code and line ranges, then rerun the same corpus
with the candidate thresholds. Commit the measured tradeoff and keep the
substantial-clone, same-module, suppression and zero-scope checks enabled:

```sh
run-with-temp env UV_NO_CACHE=1 uv run --locked --script --python 3.12 tools/tests/test_scan.py -v
run-with-temp env UV_NO_CACHE=1 uv run --locked --script --python 3.12 tools/tests/test_nightly_workflow.py -v
```

Record one-line results and log digests; keep raw logs in disposable scratch or
the producing Actions run. No test
may silently skip detector integration. Moving shared code into Builds and
deleting module copies is a separate authorized change after inspecting the
reported fragments.


## Literal npm and JavaScript/TypeScript reachability

Story 18 adds JavaScript and TypeScript without changing the 10-line/50-token
threshold, bounds, suppression rejection or cross-module-only failure policy.
A literal `npm --prefix <directory> run <script>` or declared literal npm
workspace follows its named recipe and applicable lifecycle recipes. The selected
workspace must have regular committed `package.json` and `package-lock.json`
inputs. All tracked JavaScript/TypeScript in that workspace is selected, including
Playwright configuration, global setup and reporters. Fixed installed Playwright
CLI invocations use this same scope; discovery never calls npx or evaluates a
module's configuration to determine files.

The controller's integrity-locked TypeScript 6.0.3 parser reads source through
stdin and emits syntax facts. Relative imports, literal tsconfig baseUrl/path
aliases and supported cross-language process literals extend closure beyond the
workspace. Bare package imports must be in its lock; Node builtins are external.
Computed imports, process commands, process resolution changes, indirect
TypeScript configuration and computed setup/configuration paths fail with source
diagnostics. A conservative whole-workspace selection does not excuse an unsafe
path or unresolved execution. Unmodeled package managers and recipe forms remain
fail-closed. The parser and detector are installed and signature-verified in
controller scratch before discovery, including zero-scope scans.
