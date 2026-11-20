# FrontComposer workflow pins and Debug router check

CiCd's `builds-version` selects Builds `v6.4.4` at owner commit `5ed32a5645fff72eb15ed436cdde76f8864316cc`. The proposal pins eleven calls across eight FrontComposer workflows to that release commit, `fe68718b6c074a6b500a7191e3554a1d39e17688`. The initialize-build action and reusable CodeQL, Commitlint and dependency-review workflows have identical Git blobs at the original module Builds pin `70ce9cb39` and at the selected release. The pin fixes the outer workflow source. Its legacy workflows also depend on third-party version tags. FrontComposer's weekly GitHub Actions dependency updates already cover future pin refreshes.

Quality's existing source-mode job gains one call to the FrontComposer-owned `.github/actions/test-source-router` action. It builds the Debug UI test project with MSB3277 errors enabled and runs its xUnit executable. The module owns that action, the removal of the obsolete assertion requiring Commitlint to follow `@main`, and the packed CLI Counter test already selected by primary CI. The CiCd proposal modifies only the eight caller workflows.

## Reproduce and verify

From the CiCd checkout, set `FRONTCOMPOSER` and `BUILDS` to the two absolute local repository paths. Use Bash and a temporary directory. The proposal reads Git objects, leaves the module worktree and index untouched, and writes a patch to standard output.

```bash
set -euo pipefail
: "${FRONTCOMPOSER:?set the absolute FrontComposer repository path}"
: "${BUILDS:?set the absolute Builds repository path}"
base=c1aea1732d3ce2dca299f1d9aa5ce709958ba87d
expected=8a002d3807c0c788f1a856f734cd242fb0148965
scratch=$(mktemp -d)
trap 'rm -rf -- "$scratch"' EXIT
patch="$scratch/frontcomposer-workflows.patch"
python3 tools/propose_frontcomposer_workflow_pins.py \
  --module "$FRONTCOMPOSER" --builds "$BUILDS" --revision "$base" > "$patch"
printf '%s  %s\n' f5e2d5d83adcc86c4d4f092eca289133668ec4e842772b1b22304955cfd0c375 "$patch" | sha256sum -c -
git clone --quiet --shared --no-checkout "$FRONTCOMPOSER" "$scratch/module"
git -C "$scratch/module" read-tree "$base"
git -C "$scratch/module" apply --cached --check "$patch"
git -C "$scratch/module" apply --cached "$patch"
git -C "$scratch/module" diff --cached --check "$base"
test "$(git -C "$scratch/module" write-tree)" = "$expected"
```

The recorded result is the audit baseline plus the eight workflow changes. Local qualification reproduced the patch digest and result tree. Actionlint 1.7.12 passed on all eight candidate workflows with the product action available. Parsed workflow comparisons preserved all original triggers, job permissions and steps. The only additions were the pinned references and the router step. The Debug router suite passed all 17 tests locally.

Before delivery, run the generator with `--revision` set to the exact committed FrontComposer product candidate. For a descendant of the audit baseline it checks the router action blob, removal of the incompatible test assertion and identical workflow inputs. Regenerate and qualify the resulting product tree with the corrected OIDC catalog. Hosted results and owner delivery are separate from this proposal. The [ordered module adoption plan](../../ordered-module-adoption.md) governs future registration.
