# Module setup and rendering

The registry is exactly `setup/*.yml`. Each filename stem is the GitHub repository
name, using 1–100 ASCII letters, digits, dots, underscores and hyphens, matching
[GitHub's repository-name limits](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-new-repository).
Names must be unique without regard to case. `.` and `..`, symlinks and
`Hexalith.Builds.yml` are rejected.
Builds is the runtime, never a registered module. This directory intentionally
contains no production registration until onboarding (AD-21). Synthetic inputs
belong in `tools/tests/fixtures/render/`, never here.

A setup file is the CI document without `schema` or `buildsTag`. Both are supplied
by the renderer. `{}` is valid: the pinned schema defaults to `solution: none`,
false environment flags, and empty test, hook, job, CodeQL and submodule settings.
A solution uses the `.slnx` extension. With a solution, omitted CodeQL defaults to
`[csharp]`; explicit `[]` disables analysis. Omitted nested fields also receive
schema defaults. Explicit empty collections, `false` and `null` are preserved;
invalid values, unknown fields and missing required fields without defaults fail.

For example (the actual accepted fields and constraints come from Builds' schema):

```yaml
solution: MyModule.slnx
registry: true
tests:
  integration: [test/MyModule.IntegrationTests.csproj]
  exclude:
    test/MyModule.Windows.csproj: windows-tests
hooks: [after-unit-tests]
jobs:
  windows-tests:
    runner: windows-latest
submodules: [references/MyModule.Sibling]
```

Hooks are `after-unit-tests`, `after-integration-tests` and `nightly`; their actions
and Windows job actions live at `.github/actions/<name>/action.yml` in the module.
CI runs the two test hooks; `nightly` runs only in the Release workflow's
`nightly-hook` job. Each Windows job `<name>` renders as CI workflow job ID
`windows-<name>` (the example above becomes `windows-windows-tests`), while its
action path and exclusion target keep the configured name.
The render does not inspect modules or check action existence. Exclusions must
name an enabled hook or job. The Builds submodule is implicit; `submodules` lists
additional direct dependencies. With `solution: none`, tests/hooks/jobs must be
empty and Dapr/browsers false. YAML uses the JSON/GitHub `true`/`false` spelling,
string mapping keys, no duplicate keys and JSON-compatible values.

Prerequisites: `uv`, and an initialized `references/Hexalith.Builds` submodule
whose local objects include the `builds-version` tag; rendering never fetches it.
`--lint` also requires Linux x86_64 and network access, and downloads the pinned
linters into a private temporary directory on each run.

Run these commands from the repository root, using Python 3.12 or later:

```sh
uv run --locked --script tools/render.py
uv run --locked --script tools/render.py --check
uv run --locked --script tools/render.py --project-root /path/to/cicd --check
uv run --locked --script --python 3.12 tools/tests/test_render.py
uv run --locked --script --python 3.14 tools/tests/test_render.py --lint
```

From another working directory, use an absolute script path, for example:

```sh
uv run --locked --script /path/to/cicd/tools/render.py --check
```

The default project root is derived from the script location. Rendering reads
only setup files, the explicit templates, `builds-version` and local Builds Git
objects at that exact stable tag. It never fetches or reads a module checkout.
Schemas, defaults and strict readers come from that tag, even when the Builds
checkout or HEAD differs. Both schemas and readers validate serialized output
before publication. YAML is parsed strictly too; GitHub expressions stay literal.

Each registration produces `.github/hexalith-ci.json`, `.github/dependabot.yml`
and two workflows under `rendered/<Repo>/`, plus the sibling
`rendered/<Repo>.perimeter.json`. All generated files are whole owned files.
Partial ownership is inline in the perimeter: it does not emit whole agent
instructions or Claude settings. A successful render replaces the desired tree,
removing stale repositories and artifacts while preserving `rendered/.gitkeep`.
Symlinks and output-name collisions fail before writes. `--check` reports sorted
missing, changed and extra paths and never writes; any mismatch exits nonzero.
An invalid setup or template leaves the existing output unchanged.

Render with the cause: commit changes to setup, templates, `builds-version` or
`builds-skip` together with their render (AD-5). Dependency changes to the scripts
require `uv lock --script tools/render.py` and
`uv lock --script tools/tests/test_render.py`, with both adjacent locks committed.
Default tests run offline after dependency installation. `--lint` additionally
installs the integrity-checked actionlint/zizmor pins from the Builds tag and scans
explicit nonempty temporary fixture paths with online audits. Supply a read-only
`GH_TOKEN`, `GITHUB_TOKEN` or `ZIZMOR_GITHUB_TOKEN` through the environment; failed
or incomplete scans fail validation. No legacy finding exceptions apply.

Dependabot maintains module-local NuGet versions only when a solution exists:
one NuGet entry at `/`, excluding `references/**`, weekly Monday at 06:00 Etc/UTC,
at most five open PRs, and prefix `build(deps)` without extra scope. No-solution
modules receive `version: 2` and `updates: []`. Actions, submodule, npm, pip and
Docker updates are not enabled. Builds' imported package catalog changes through
Builds releases. A module agent or maintainer reviews and merges after green CI,
preserving `build(deps)`; a deliberately releasable security fix uses `fix(deps)`.
There is no automerge workflow or new agent permission.

Story 10-2 replaces two deliberate interim partials, then re-renders with that
policy change. Until then every marker body is exactly
`CI/CD ownership instruction placeholder; replaced by story 10-2.` plus LF, and
the owned deny values are `[]`. These valid v1 placeholders do not complete
CAP-11. Rendering does not deliver, onboard, dispatch, publish, enforce drift,
check acceptable GitHub releases, or orchestrate global checks.

## Candidate validation

Run either shared global checks or the full validation verdict from the root:

```sh
uv run --locked --script tools/check_global.py
uv run --locked --script tools/validate.py
uv run --locked --script tools/validate.py --project-root /path/to/cicd
```

Both commands require Python 3.12 or later and derive the default project root
from the script location. Use an absolute script path from another directory.
Commit the render with its cause before validating: global checks compare the
candidate `HEAD` paths, bytes and modes under `rendered/` with the working copy
and a fresh read-only render. The pin, registry and used templates must also
match `HEAD`; unrelated planning, evidence and tool changes may remain in the
working tree. Neither command writes generated files or module state.

The CiCd candidate must be a Git checkout. A separate Builds checkout at
`references/Hexalith.Builds` must have the complete local objects and tags for
`builds-version`; no other module checkout is needed. The workflow checks out
Builds `main` with `fetch-depth: 0`, without nested submodules or persisted
credentials. Its worktree and HEAD never supply contract bytes: schemas,
strict readers, callable interfaces and linter pins are exported from the exact
tag's Git objects. The published `v5.1.0` release at
`9ebc31f606bc02f8a0ec2f1ec344127e2468c6b4` satisfies the perimeter schema/library
prerequisite. An older or incomplete pin fails explicitly; newer checkout files
cannot substitute for the selected release.

Validation requires Linux x86_64, outbound HTTPS to GitHub for release and tag
metadata, linter archives and online zizmor audits, and anonymous Git access to
each registered module's live `main`. Supply a read-only `GH_TOKEN` or
`GITHUB_TOKEN` privately through the environment. In Actions the only credential
is the job's `GITHUB_TOKEN` with `contents: read`. Unavailable or malformed API
responses fail verification, including authorization errors. Module reads use
anonymous shallow clones with no checkout execution, recursive submodules,
credentials, helpers or extra headers. Action availability comes from committed
live-main trees, independently of local module checkouts and pinned gitlinks.

`check_global.py` checks reproducibility, committed render, generated schemas
and strict readers, actual rendered callers and permissions, tool suites, pinned
actionlint and online zizmor, and acceptable Builds publication. The selected
release must be published, immutable, authored by `github-actions[bot]`, agree
with the locally peeled tag, and be an ancestor of live Builds `main`. This is
the same global entry point that the future nightly bump will invoke. It writes
nothing to stdout and logs each check to stderr. It exits 0 only when every
global check passes; otherwise it reports each failed or incomplete check and
exits 1. The shared runner executes tool tests without `--lint`; representative
fixture online lint remains the separate `test_render.py --lint` command above.

`validate.py` invokes global checks once, then independently checks every
registration's candidate CI document, direct-submodule declaration and gitlink,
enabled hook/job names and exclusion targets, and live action availability. It
prints exactly one compact JSON object on stdout, for example
`{"global":true,"modules":["Hexalith.Example"]}`. `modules` is sorted and contains
only passing repository stems from this registry. Diagnostics and tool logs go
to stderr. When `GITHUB_OUTPUT` is set, the same JSON is appended as one
`verdict=` record. Exit 0 requires global checks and every module to pass;
otherwise it emits the verdict and exits 1. A global failure preserves modules
whose independent checks pass; an unusable registry or unavailable selected
contract cannot certify module names.

The intentionally empty production registry is valid and yields
`{"global":true,"modules":[]}` when global checks pass. Nonempty validation
fixtures live under `tools/tests/fixtures/validate/`; run them with
`uv run --locked --script --python 3.12 tools/tests/test_validate.py` (or Python
3.14). Dependency changes require adjacent locks from
`uv lock --script tools/check_global.py`, `uv lock --script tools/validate.py`
and `uv lock --script tools/tests/test_validate.py`. The story 10-2 ownership
placeholder and empty deny values above remain intentional.

`deliver.yml` currently runs only this read-only `validate` job on pushes to
`main`, pull requests, hourly at minute 47 and manual dispatch. Its `verdict` job
output carries the JSON even after ordinary validation failures. Main runs use
noncancelling concurrency group `deliver`; all other refs use cancelling
`deliver-validate-<ref>`. Delivery and App checks belong to a later story.
