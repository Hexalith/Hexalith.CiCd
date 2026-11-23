# Hexalith.CiCd
Maintain harmonized Hexalith CI/CD workflows across modules.

[Nightly releases](docs/nightly.md) dispatch Builds and adopted modules at
02:17 UTC, collect their exact run outcomes, publish validated ready drafts,
and report every target's verdict and run link.

## Linux maintainer quickstart

Start with Bash, Git, curl and the usual Linux command-line utilities. Bootstrap
needs HTTPS access to Astral, GitHub (including release downloads), PyPI and its
package files. No GitHub credential or product module checkout is needed here.

Use Git 2.41 or later for Builds perimeter repair. It uses `GIT_ATTR_SOURCE`
to hash repaired entries with attributes from the selected index. Older Git
can pick up a conversion filter from a dirty worktree during repair.
[Git 2.41 release notes](https://github.com/git/git/blob/v2.41.0/Documentation/RelNotes/2.41.0.txt)

Use the installed `run-with-temp` wrapper when available. On a new machine,
define this Bash function in the current shell; it creates private scratch,
preserves the command's exit status and removes scratch on exit. Run foreground
commands and wait for any children before returning. Keep results outside scratch;
record a one-line result and a SHA-256 digest instead of committing raw logs.

```bash
if ! command -v run-with-temp >/dev/null 2>&1; then
  run-with-temp() (
    set -euo pipefail
    job_tmp=$(mktemp -d "${TMPDIR:-/tmp}/hexalith-job.XXXXXXXX")
    trap 'rm -rf -- "$job_tmp"' EXIT
    export TMPDIR="$job_tmp" TMP="$job_tmp" TEMP="$job_tmp"
    "$@"
  )
fi
```

Run this from any directory. It installs the workflow's pinned **uv 0.13.7**
and managed **Python 3.12** into scratch, clones the parent without recursion,
and initializes only Builds at the parent's gitlink. Fetch the selected tag,
both renderer fixture tags (`v6.0.6` and `v6.1.0`) and the `v5.1.0`
global-suite fixture tag. The renderer reads local tagged Git blobs. The
selected tag comes from [`builds-version`](builds-version).

```bash
run-with-temp bash <<'BOOTSTRAP'
set -euo pipefail
export UV_CACHE_DIR="$TMPDIR/uv-cache"
export UV_PYTHON_INSTALL_DIR="$TMPDIR/uv-python"
export UV_PYTHON_BIN_DIR="$TMPDIR/bin"
export UV_PYTHON_PREFERENCE=only-managed
export PYTHONDONTWRITEBYTECODE=1
curl --fail --location --silent --show-error \
  https://astral.sh/uv/0.13.7/install.sh -o "$TMPDIR/install-uv.sh"
UV_UNMANAGED_INSTALL="$TMPDIR/bin" sh "$TMPDIR/install-uv.sh"
export PATH="$TMPDIR/bin:$PATH"
uv --version
uv python install 3.12

git -c submodule.recurse=false clone --no-recurse-submodules --branch main \
  https://github.com/Hexalith/Hexalith.CiCd.git "$TMPDIR/cicd"
cd "$TMPDIR/cicd"
git -c submodule.recurse=false submodule update --init --checkout -- references/Hexalith.Builds
builds_tag=$(cat builds-version)
git -c submodule.recurse=false -C references/Hexalith.Builds fetch --no-recurse-submodules origin \
  "refs/tags/$builds_tag:refs/tags/$builds_tag" \
  refs/tags/v6.0.6:refs/tags/v6.0.6 refs/tags/v6.1.0:refs/tags/v6.1.0 \
  refs/tags/v5.1.0:refs/tags/v5.1.0

uv run --locked --script --python 3.12 tools/render.py --check
uv run --offline --locked --script --python 3.12 tools/tests/test_nightly_runtime.py -v
test -z "$(git status --porcelain --untracked-files=no)"
test "$(git -c submodule.recurse=false submodule foreach --quiet 'echo "$sm_path"')" = references/Hexalith.Builds
git rev-parse HEAD 'HEAD^{tree}'
git -C references/Hexalith.Builds rev-parse "refs/tags/$builds_tag" "refs/tags/$builds_tag^{commit}"
echo 'PASS: locked render, offline controller suite, unchanged tracked files; only Builds initialized'
BOOTSTRAP
```

To replay the archived [30-2 qualification](_bmad-output/planning-artifacts/sprint-change-proposal-2026-11-19.md#30-2-clean-checkout-qualification--22-november-2026),
optionally insert `git fetch --no-tags origin 307405aba85e587982b69d6ce5847ab2c06000a3`
and then `git checkout --detach FETCH_HEAD` immediately after the bootstrap's
`cd "$TMPDIR/cicd"`, before submodule initialization.

`--locked --script` uses each script's adjacent `.py.lock`; do not regenerate
locks to make qualification pass. The controller suite has no dependencies and
uses injected HTTP transport and local Git fixtures, so its `--offline` run
needs no package or GitHub access after interpreter bootstrap. The render step
can download its locked Python dependencies. These results establish local
rendering and offline controller behavior only.

## Online validation

The live module registry is [`setup/`](setup/); registrations include modules
awaiting adoption. See the [duplicate-scan guide](docs/duplicate-scan.md) for
source coverage, output retention and the focused real-detector command.

The quickstart removes its checkout and toolchain on exit. To qualify online
in that same fresh checkout, insert the selected command below inside
`BOOTSTRAP`, after the offline suite and before the final assertions. Omit its
`run-with-temp` prefix because the outer wrapper already owns scratch. For an
existing checkout, use the wrapped
commands as shown with the same pinned uv and Python, local Builds tag objects
and adjacent locks. `UV_NO_CACHE=1` puts uv's temporary cache and environments
under the wrapper's scratch and propagates to child uv processes, including
global validation's tool suites. Install **Node 24 with npm** and compatible
**PowerShell 7** (tested: **7.6.2**; `pwsh` with the native `ModuleAnalysis`
parser API). Allow npm
downloads from `https://registry.npmjs.org` and signature/provenance verification
services, GitHub Git
and API access, and GitHub release/archive downloads for pinned auditing tools.
Full global validation targets **Linux x86_64**. Supply the existing read-only
audit credential through `GITHUB_TOKEN` or `GH_TOKEN` for release/bootstrap API
proofs and online zizmor audits. It needs read access to Hexalith.CiCd contents
and bootstrap objects and Hexalith.Builds release and tag objects; never print
or commit it.

```bash
run-with-temp env UV_NO_CACHE=1 uv run --locked --script --python 3.12 tools/check_global.py
run-with-temp env UV_NO_CACHE=1 uv run --locked --script --python 3.12 tools/validate.py
```

`check_global.py` checks committed inputs/renders, publication and bootstrap
proofs, workflow audits and all tool suites, including real detector integration.
`validate.py` also verifies registered modules' live `main` trees through
anonymous reads and emits the delivery verdict. It runs global checks itself;
choose the entry point needed. Keep npm signature verification and online audits
enabled. A refused prerequisite or a failed or unexecuted online check remains
unproven even when the offline quickstart passes.

## BMAD Loop worktrees

BMAD Loop worktrees initialize the direct submodules declared in `.gitmodules`
at their pinned commits. Nested submodules stay uninitialized, even when Git's
`submodule.recurse` setting is enabled. Initialization failures stop that unit
before its coding session starts.

After setting up BMAD Loop on a new machine, enable the project hook:

```bash
bmad-loop plugins enable direct-submodules
```

The hook runs when worktree isolation is selected (`[scm] isolation = "worktree"`
in `.bmad-loop/policy.toml`).
