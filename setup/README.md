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
