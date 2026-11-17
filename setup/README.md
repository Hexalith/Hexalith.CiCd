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

When the selected Builds release declares `ciTimeoutMinutes`, the renderer
materializes its default of 30 and forwards it to the shared workflow's
`job-timeout-minutes` input. An explicit integer from 1 to 360 selects a longer
or shorter build/test budget. Older pins retain their original contract and
caller; update `builds-version` to the compatible published release before
using the new registry field. Choose a module allowance from its measured
serialized workload.
Contracts that also declare the explicit native `job-timeout-minutes` override
retain that override's precedence over `ciTimeoutMinutes`.

`additionalSdkVersion` optionally selects one exact stable SDK through shared
CI's existing `additional-sdk-version` input. It also reaches independently
prepared jobs. EventStore needs SDK 10.0.404 for its SDK10 generator-refusal and
net10.0 reference-pack controls; module actions install no SDK. Use the field
only after the selected published immutable Builds contract supports it.

Hooks are `after-unit-tests`, `after-integration-tests` and `nightly`; their actions
and custom job actions live at `.github/actions/<name>/action.yml` in the module.
CI runs the two test hooks; `nightly` runs only in the Release workflow's
`nightly-hook` job. Each Windows job `<name>` renders as CI workflow job ID
`windows-<name>` (the example above becomes `windows-windows-tests`), while its
action path and exclusion target keep the configured name.
The render does not inspect modules or check action existence. Exclusions must
name an enabled hook or job. The Builds submodule is implicit; `submodules` lists
additional direct dependencies. With `solution: none`, tests/hooks/jobs must be
empty and Dapr/browsers false. YAML uses the JSON/GitHub `true`/`false` spelling,
string mapping keys, no duplicate keys and JSON-compatible values.

The producer-preparation interface adds two optional nullable fields. Old complete
documents may omit them; the renderer materializes the defaults from the selected
released schema. `moduleManifest` selects a regular repository-relative JSON
manifest and prepares the exact pinned module CLI before the first project
evaluation. Its active package catalog is the accepted delivered Builds release.
Platform's actual released identity, supported tool range and historical catalog
pin remain independently verified provenance. Legacy producer source/package
commands retain their original tuple checks.

`windowsCheckout` contains `exclude: [{path: archive/directory, tree: <full-tree-oid>}]`.
This centrally reviewed setting binds immutable non-product archive directories.
The loader rejects unsafe Windows paths, aliases, overlaps and exclusions of
solution, SDK, manifest, actions or direct dependencies. Shared CI exports the
validated paths, accepted authority, exact source revision and compact checkout
JSON to Windows. Remote `prepare` consumes those outputs, qualifies the full
materialized complement using native protected Git and uses cone sparse-index
checkout. It keeps NTFS protection enabled and initializes direct dependencies
without the parent submodule helper. Null preserves ordinary checkout. Windows
uses native Python 3.12+ already on the runner and installs no extra environment.

Preparation persists one private producer workspace through evaluation, restore,
build, tests and hooks. Every reuse verifies source identities and import bytes.
Local checking fetches and initializes nothing and removes scratch on completion.
Nightly release prepares before publication discovery while retaining its audited
restore and release targets. The separate candidate-qualification authority is
local product proof only; CI, the normal checker, Windows and release reject it.

## Adoption execution extensions

The following additive fields require a published Builds tag whose exact schema,
strict reader, workflow and action interfaces supply them. Updating checkout
files alone does not enable them. Keep `builds-version` and production
registrations unchanged until the separate Builds infrastructure release is
published and qualified.

`releaseTimeoutMinutes` and `nightlyTimeoutMinutes` bound the audited release
build and existing nightly hook respectively, from 1 through 360 minutes. Omission
keeps their 45-minute defaults. `jobs.<name>.timeoutMinutes` similarly bounds
one independently prepared custom job; its default is 30 and private jobs are
limited to 180 minutes. Set limits from measured
workloads. A 360-minute mutation allowance is not evidence of elapsed duration.

For example, a future compatible registration can express isolated product lanes:

```yaml
jobs:
  authenticated-routes:
    runner: ubuntu-latest
    timeoutMinutes: 90
    matrix:
      include:
        - {id: route-one}
        - {id: route-two}
        - {id: route-three}
        - {id: route-four}
    maxParallel: 4
    setup: {dapr: true, browsers: true}
  mutation-segments:
    runner: ubuntu-24.04
    trigger: nightly
    resourceProfile: mutation
    timeoutMinutes: 360
    matrix:
      include:
        - {id: happy-path}
        - {id: error-handling}
  mutation-summary:
    runner: ubuntu-24.04
    trigger: nightly
    resourceProfile: mutation
    timeoutMinutes: 360
    needs: [mutation-segments]
    runAfterFailure: true
```

Each matrix record has a unique kebab-case `id` and literal string values. Each
case gets a fresh runner, checkout, Release build, shared setup and product
action. `fail-fast: false` preserves the other cases when one fails. `needs`
forms a same-trigger dependency DAG. `runAfterFailure` permits an aggregate to
inspect failed dependencies without changing their failed verdicts. Product
actions exchange reports through artifacts with names including the job and
case identity; a serial hook cannot replace these isolated workers.

Hosted runners are `ubuntu-latest`, `ubuntu-24.04`, `windows-latest` and
`macos-latest`. Existing minimal Windows/macOS jobs keep their original
`windows-<name>` IDs. Linux jobs use `custom-<name>`. The `mutation` resource
profile comes from the selected Builds schema's `x-resource-profiles` bytes:
the authenticated SDK container digest, four CPUs, 10 GiB memory and the same
swap cap. Builds installs Python and patch before preparation, selects its
supported Python interpreter, and records cgroup limits. Module actions do not
reimplement this preparation.

`trigger` defaults to `ci`. A `nightly` or `manual` job adds the owned
`qualification.yml` caller. Its nightly schedule is centrally defined here at
02:37 UTC, independently of the release scheduler. A main-branch manual dispatch
selects `nightly` or one named manual job, together with its prerequisites.
This workflow has no publisher. Successful qualification provides adoption
evidence; it grants no release or publication permission and does not replace CI.

Protected live qualification uses a manual-only private job:

```yaml
jobs:
  azure-conformance:
    runner:
      group: payload-protection-azure-private-ephemeral
      labels: [self-hosted, linux, x64]
    trigger: manual
    environment: payload-protection-azure-conformance
    timeoutMinutes: 45
    secrets:
      AUTHORITY_JSON: PAYLOAD_AZURE_AUTHORITY_JSON
      CUSTODY_JSON: PAYLOAD_AZURE_CUSTODY_JSON
```

Every selected private lane, including dependencies of a selected aggregate,
waits for a fresh shared `qualification-ci` run at the dispatch SHA. Its exact
successful `source-sha` and the explicit dispatch `authority-sha256` go to Builds'
`prepare` in `environment: preserve` mode. Builds validates the request before
checkout, builds once and retains the owner's Dapr/runtime fixture. Private
setup overrides are rejected. The legacy `secrets: [NAME]` plus
`preparation: build-only` form follows the same path; mapped secrets may also
state `preparation: build-only` explicitly.

The environment's protection, runner-group isolation/ephemerality and secret
scope require separate live verification before adoption. Secret values reach
only that product action step, never general CI or shared preparation. Dispatch
`parameters` is JSON for product authority identifiers and modes, never credentials.
The product action validates its authority/custody and real fault eligibility.
The catalog Dapr tuple is not a replacement for its historically qualified tuple.

Extended actions receive `HEXALITH_JOB_NAME`, `HEXALITH_JOB_PARAMETERS` (the JSON
matrix record, or `{}`), `HEXALITH_JOB_NEEDS` (dependency outcomes) and
`HEXALITH_QUALIFICATION_PARAMETERS` (manual parameters, otherwise `{}`). Private
lanes also receive trusted `HEXALITH_AUTHORITY_SHA256` and `HEXALITH_SOURCE_SHA`.
Actions
must parse this data without interpolating it into shell code, retain ownership
of their product hosts/backends and clean their own resources. Credentials must
not be copied into reports or artifacts.

Per-job `setup` overrides only shared environment settings: `dapr`, `browsers`,
`registry`, `aspire`, `npmWorkspaces`, `dotnetTools` and `prerequisites`. It does
not alter test classification. `prerequisites` is also available at the module
level: exact paired `nodeVersion`/`npmVersion`, `apt`, `tlsTrust` and the explicit
`daprProfile: catalog`. The runtime refuses a mismatched npm version, unsupported
Dapr profiles and unsafe workspace inputs. No historical runtime promotion is
implied. Browser product startup and assertions remain in enabled actions.

An enabled action can use Builds' `Github/qualification-tools` with a product-owned
`hexalith.qualification-tools.v1` manifest of exact official assets and hashes.
Staging is isolated. Its optional `dapr-runtime-version` uses the shared full
initializer for an exact runtime >=1.18.0 with the verified official CLI named
`dapr`. It requires a fresh hosted Linux worker, shared `dapr` setup disabled,
and no existing Dapr home/receipt. It exports a job-bound initialization receipt;
product compatibility and eligibility assertions remain in the action. Private
workers preserve owner preparation and cannot use this initialization option.

`tests.additional` explicitly admits test projects outside the selected solution
to shared Release restore/build and discovery; non-test or missing projects fail.
`tests.reports.trx: true` collects native per-project results. Optional
`tests.reports.coverage` declares required `projects`, `lineScope`,
`minimumLine`, `lineComparison` (`at-least` or `greater-than`), `branchTargets`
and `minimumBranch`. Scope prefixes may end in `/`; branch targets name exact
source files. A threshold requires a nonempty corresponding scope. Missing,
empty or invalid required reports fail. Reporting without thresholds adds no
gate. Preserve each product's existing scopes/comparisons; Tenants retains strict
line coverage greater than 80 and branch coverage at least 100 on its named files.
The shared local checker uses the same unit report rules in stages 1–3; hosted
integration, custom jobs and qualification still require separate evidence.

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
and the CI/release workflows under `rendered/<Repo>/` (also `qualification.yml`
when qualification jobs are enabled), plus the sibling
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

The [ownership block](../templates/partials/ownership-block.txt.j2) is the
canonical module-agent CI/CD contract. CiCd owns workflows, CI configuration,
Dependabot, the Builds gitlink and its `.gitmodules` section, the three delivered
instruction blocks, and the required Claude deny entries. The shared perimeter
library supplies the instruction markers and merges those blocks and deny
entries while preserving foreign text, allow/deny entries and unrelated settings.

The [deny list](../templates/partials/deny-entries.json.j2) uses project-local
`Edit(/path)` rules for whole-owned files and the Builds subtree. Launch Claude
Code from the module root: a project's `/path` rule anchors at the primary
working directory. Reads remain available. Do not put these rules in
machine-wide settings. File rules cannot target JSON keys, marker ranges or a
single `.gitmodules` section; the instructions and shared guard protect those
owned portions. See [Claude's permission documentation](https://code.claude.com/docs/en/permissions#read-and-edit).

Keep module gates that check compilation, tests, security and dependencies,
commit format or package publishing, including module-specific product checks
as enabled custom actions. Delete module gates that check CI itself, agent
tooling, story evidence or workflow YAML text, and tests that assert workflow
YAML. Apply the [gate rule](../AGENTS.md) during migration before enabling hooks
or jobs. Agents fix product failures, report pipeline defects and credential
refusals, and require a successful `python3 references/Hexalith.Builds/check.py`
before pushing without audit/test bypasses or skip markers/trailers. Product
branches start from freshly fetched current `main`. GitHub permits PR Update
branch with the restricted module credential even when it imports workflows;
do not use it to import owned CI/CD changes. Fetch current `main`, create a new
product branch, and reapply only product changes. Releases follow the central
nightly process.

Rendering does not deliver, onboard, dispatch, publish, enforce drift, check
acceptable GitHub releases, or orchestrate global checks. Updating these policy
partials does not register or adopt a production module.

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
each registered module's live `main`. The tool suites include the duplicate-scan
suite, which installs the integrity-pinned jscpd with the real detector, so
validation also requires Node 24 with npm on `PATH` and outbound HTTPS to
`registry.npmjs.org` for `npm ci --ignore-scripts` and `npm audit signatures`.
The nightly bump job sets up the same pinned Node 24 before its global gate. Supply a read-only `GH_TOKEN` or
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
the same unchanged global entry point invoked by the nightly bump producer. It writes
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
and `uv lock --script tools/tests/test_validate.py`.

`deliver.yml` runs this read-only `validate` job on pushes to
`main`, pull requests, hourly at minute 47 and manual dispatch. Its `verdict` job
output carries the JSON even after ordinary validation failures. Main runs use
noncancelling concurrency group `deliver`; all other refs use cancelling
`deliver-validate-<ref>`.

## Delivery and repair

On `main`, the second job enters `cicd-app` after validation even when validation
fails. The immutable bootstrap is checked out into `.delivery-bootstrap` from
the literal source commit in the workflow. It fetches committed CiCd objects
anonymously, validates the exact JSON verdict, and verifies every accepted
`delivered/<Repo>` ref is ancestral to current CiCd `main`. A true global verdict
selects candidate tools. Otherwise it selects the newest valid accepted target
in `git rev-list --topo-order main`; missing accepted tools fail closed, with no
candidate fallback. Only regular `tools/` blobs are exported. Setup/workflow YAML
and module executables are never parsed or run in the privileged job.
A manual cancellation stops further mints, accepted-ref advances and module
writes; finalization and report upload still run and mark unstarted slots failed.

The selector supplies seventeen sequential ordinal slots from the committed
registry and accepted-ref union. The workflow has no second module-name list.
Overflow fails before writes; an empty registry succeeds without module tokens
or accepted-ref writes. A module's scoped mint failure or controller failure
does not prevent later slots. Each passing module must satisfy both anonymous
validation and the closed App checks (installation access, AD-21 rulesets,
CodeQL default setup off, Dependabot security updates off, retention 90 days).
Only then can its accepted ref advance forward to the exact candidate SHA.
An older run reports `superseded by <full-sha>` and applies current accepted state.

Every valid accepted ref is reapplied, including skipped modules and failed
global runs. The writer verifies that ref's exact published immutable bot Builds
release, remote tag object, peeled source, live-main ancestry, and released
perimeter schema/library before loading code or writing the module. The current
`v5.1.0` release supplies this prerequisite. Its library applies every perimeter
entry to a private index from anonymous live module `main`, preserving foreign
content. An unchanged tree produces no commit. A changed tree gets one
`build(cicd): apply …` commit whose sole parent is fresh module `main`. Only a
genuine non-fast-forward with changed main retries, at most three reapplications;
the writer never rebases or force-pushes.

Each entered job attempts one `hexalith-delivery` artifact containing only
`delivery.json`, written atomically from bootstrap initialization onward. Its
`schema`, run ID/attempt/event, candidate SHA, tools-source SHA (nullable),
`global`, `failed`, `failures`, and `freshness` describe the run. Deterministic
`modules` rows contain `repository`, `accepted_sha`, `advancement` (`advanced`,
`unchanged`, `superseded`, `skipped`, `failed`), `application` (`pushed`,
`unchanged`, `no-ref`, `failed`), `pushed_sha`, `retries`, sanitized `reasons`,
and `processed`. Advancement and repair are independent. Any failed global or
module check, unavailable scope, stale/unreadable nightly history, or failed
write makes finalization fail after all repairs. Supersession and an empty
registry alone do not fail. On hourly runs, valid empty nightly history is not
activated; a latest main nightly creation time exactly 26 hours old passes,
and older fails regardless of the nightly conclusion. A nightly workflow absent
from a successful workflow inventory is not activated; inventory errors fail.

Only the pinned mint action receives the `cicd-app` private key and client ID.
CiCd tokens have Contents/Workflows write and Actions read; module tokens have
Contents/Workflows write, plus Administration read only when checks are needed.
Tokens are private process inputs, never JSON state, files, URLs or command
arguments; Git receives a process-local header scoped to GitHub HTTPS. No module
or Builds source receives the private key. Processes discard inherited Git,
Python, helper, attribute and credential configuration before tagged code loads.
All work observes a 36-minute soft deadline within the 40-minute job, with token
age conservatively measured from selector startup and limited to 50 minutes.

To maintain the bootstrap, first test and commit the selector, runtime and
controller, obtain the full commit with `git rev-parse HEAD`, and push that source
so GitHub can fetch it. Only afterward change the workflow's literal checkout
SHA. Never point it at the candidate, a branch, a fabricated hash or a placeholder.
The global check reads both bootstrap files at the manifest's immutable source
SHA through the read-only contents API and verifies their SHA-256 digests.
Refresh the frozen `tools/tests/fixtures/delivery-bootstrap/` copies and manifest
digests when changing that pin; they support offline tests in shallow checkouts.
Re-run the four `test_delivery_*.py`/`test_deliver.py` scripts with adjacent locked
PEP 723 environments on Python 3.12 and runner Python, then the existing suites
and global checks outside `cicd-app`. Hosted qualification records the exact
source/run/artifact identities and inspected report in
`_bmad-output/specs/spec-cicd/evidence/7/verification.md`. Production setup files
remain empty until onboarding; delivery is infrastructure, not adoption.


## Nightly Builds version policy

`builds-version` pins one exact stable Builds tag. Nightly considers only its
current major and the newest published, immutable bot release whose remote and
locally peeled tag identities agree and whose commit is ancestral to Builds
main. Version comparison is numeric (`v5.10.0` follows `v5.9.0`). A different
major requires an explicit change here.

`builds-skip` contains one exact stable tag per line; empty lines are ignored.
Do not use comments, ranges or prereleases. To retain a rollback, restore the
older pin and list each bad newer tag in `builds-skip`, then render and commit
the cause with its output. Nightly leaves that rollback alone unless another
newer acceptable unskipped release exists. It makes at most one automatic bump
per UTC night, identified by the nightly run's creation date across reruns.

The secretless producer commits and globally validates its candidate before a
separate stdlib writer authenticates the object handoff and independently
constrains the diff. Only existing rendered regular files and the pin can
change automatically; a newly introduced CI JSON key must equal the exact tagged
schema's default. Setup, templates, adoption and skip policy remain explicit
maintainer changes. Failed validation or fresh-main/release races fail closed.
Confirmed bumps wait for delivery and every actually pushed module's first
qualifying CI result, including repair pushes. Production setup remains empty;
nightly fixtures do not adopt a module. See [nightly operation and rollback](../docs/nightly.md)
and [hosted transport qualification](../docs/nightly-bump-qualification.md).

## Nightly duplicate scan registry

The committed setup filenames also register the nightly duplicate scan. Every
registered module is scanned at its anonymous live `main`, including modules
not yet adopted and dormant `.github/actions/**` directories. Builds is excluded,
and the registry is capped at 17 modules. The scan recursively follows supported
local YAML, shell, PowerShell and Python sources and Python imports. Every literal
that names a tracked script, and every local module that a literal `-m` operand
names or a `-c` operand imports, is included from every candidate base, whatever
consumes it. Missing, unsafe, cross-language or unresolved local calls and
unmodeled indirection fail coverage with a source diagnostic. Unmodeled
indirection includes stdin-fed interpreters, import-path, module-path or `PATH`
changes, reflective process APIs, and task or test runners with tracked recipes
or tests.

CiCd's committed jscpd 5.4.3 policy uses weak mode with 10 lines and 50 tokens;
module detector config, ignore files and suppression directives cannot waive it.
Only fragments crossing module boundaries fail the duplication gate. An empty
registry or a successfully fetched module without actions reports explicit zero
scope. Fetch, discovery, tooling and report failures remain red while healthy
siblings still contribute observations. Scan failure preserves the report and
summary and permits the later Builds bump and keepalive jobs. It never adopts or
edits a module. See [scan scope, reports and threshold calibration](../docs/duplicate-scan.md).

### Isolated build-order references

The managed package producer supports an additive `HexalithIsolatedBuildContract`
metadata marker on a `ReferenceOutputAssembly=false` project reference. It names
a tracked, closed `hexalith.isolated-build.v1` JSON declaration containing
`owner`, `projects`, `roots`, `framework`, `propertyPrefix`, `properties`, `props`
and `targets` (plus the `schema` identifier). The owner must be non-test,
non-packable, non-publishable and disable default compilation. The declaration
binds the exact source/import roots and child graph to the authenticated module
revision and actual active catalog; ordinary legacy references retain their
existing closed-property checks.

This interface admits only Release package mode, locked restore, exact declared
imports, the preserved inherited common-targets chain, empty warning demotions
and options under a nonreserved namespace. The producer verifies source Git
identities and independently regenerates the SDK's exact NuGet imports/assets
in private scratch against the tracked successor lock. It admits no arbitrary
obj files or unrestricted AdditionalProperties. See the [source qualification
contract](../_bmad-output/specs/spec-cicd/evidence/16/implementation-and-verification.md).

Builds v6.2.0 adds the closed `buildProjects` form
`{id, project, isolatedContract}` for these adapters. It requires managed
`moduleManifest` preparation and a committed descriptor whose owner, exact
build-order references, framework and nonshipping flags match the evaluated
adapter. Shared code restores and builds it in separate SDK processes after the
root solution, under the same authenticated preparation lifetime. The adapter
stays outside the root solution; frozen fixture projects remain unchanged.
Every isolated SDK invocation, including preflight, disables node reuse so the
.NET 11 build server cannot share SDK resolver state across these processes.
Linux, Windows, local checking and release preparation use the same route.
Product hooks execute the built tests and never build the fixture.

This form preserves the fixture's SDK selection and canonical build outputs. It
does not publish finite-version artifact mappings or relax the existing
`{id, project, versions}` form's restrictions. Managed catalog snapshots remain
immutable: an unseeded consumer is evaluated against the pinned catalog without
rewriting the prepared snapshot. Legacy catalog caching retains its behavior.
Select an acceptable release that implements and qualifies this support before
using the new declaration in a production registration.

Protected source checkout fetches the exact selected commit with complete ancestor
history, without recursively initializing dependencies. This preserves retained
product assertions that read genuine historical objects. Archive exclusions limit
materialization; they do not truncate Git history. Direct identity checkouts remain
limited to their explicitly recorded pins and required release tags.

Windows callers forward the additive preparation outputs when the selected
released schema defines both nullable knobs. Older pinned contracts retain their
original caller inputs, so introducing this source interface does not change
existing module defaults before the supporting release is selected.


### Platform prerequisite source contract

The next supporting Builds release adds `publishedBuilds: null` and
`buildProjects: []`; existing selected releases and production registrations stay
unchanged. `publishedBuilds` names a committed closed shared-release tuple JSON,
mutually exclusive with `moduleManifest`. Shared preparation authenticates the
historical signed tool independently of the active accepted catalog and exports
`HexalithBuildsPublishedToolRoot` before evaluation.

`buildProjects` contains up to 32 `{id, project, versions}` declarations. IDs are
unique kebab-case; projects are committed non-test `.csproj` consumers outside
package discovery. Only `HexalithEventStoreVersion`, `HexalithTenantsVersion` and
`HexalithMemoriesVersion` exact stable selections are accepted. Preparation and
Linux execution are required; custom platform jobs are rejected. Shared code
builds each case with private SDK artifacts and publishes the JSON environment
mapping `HexalithBuildProjects` for read-only product actions through the job.

Packable projects may evaluate `HexalithVerifyPublishedPackage=true`, consistently
across TFMs, to require public NuGet signature verification and exact original
nonsignature member bodies. No module callback runs in the privileged publisher.
These source additions require a qualified immutable Builds release before use.
