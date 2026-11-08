# Enforcement

How CI/CD changes made outside this repository are blocked and undone, and how custom actions are kept module-specific. Serves CAP-7, 8, 9, and 11. The mechanics are in the architecture spine (AD-4, AD-6 to AD-8, AD-14).

## Layer 1: token scoping

- Module agents use a fine-grained token, limited to the module repositories, as their git and `gh` credential. It has Contents and Pull requests write access, and no Workflows, Administration, Actions, Variables, or Secrets write access. So GitHub rejects any push that touches `.github/workflows/**`, and any workflow dispatch.
- Agents working in this repository use a second token, scoped to Builds and this repository only, in interactive sessions.
- Agent sessions never run with the maintainer's personal `gh` login, which has the `workflow` scope.
- Limits:
  - This layer doesn't cover owned files outside `.github/workflows/`. Layer 2 covers them.
  - Org-wide agent Apps (`claude`, `chatgpt-codex-connector`, `cursor`) hold Workflows write access on every repository, and the org can't remove it. Only layers 2 and 3 cover them. `semgrep-app` is uninstalled from the managed repositories if Semgrep is unused.

## Layer 2: the guard

The guard is owned by Builds. It runs first in every CI run and takes seconds.

1. It reads the module's expected owned state from this repository's `delivered` branch, by shallow git clone. That branch holds only renders that passed validation. This repository is public, so no token is needed, and module agents can't change it.
2. It compares the module with the expected state (perimeter in SPEC Constraints, entry kinds in AD-4). It also checks that:
   - every enabled hook and job action exists;
   - the custom actions avoid the deny list below;
   - no module MSBuild file waives NU1903 or NU1904 (`NoWarn`, `NuGetAuditSuppress`);
   - commit messages pass commitlint.
3. **On a PR or a push to another branch:** it fails with the diff and the message "CI/CD is owned by Hexalith.CiCd. Fix the product code, not the pipeline."
4. **On a push to `main`:** it fails the same way. A separate restore job then:
   - writes the expected state in one commit, skipping `.github/workflows/**`, which `GITHUB_TOKEN` can't write;
   - dispatches CI on `main`, so the restored files are tested right away.
5. **On `workflow_dispatch`:** it checks, and never restores.

It restores the files instead of running `git revert`, because an agent's commit usually mixes product changes with the CI/CD edit.

The release re-runs the same check on its release SHA, so a drifted caller can't ship.

Known effects:
- A module whose workflow files were edited stays red until the next delivery, within an hour.
- The restore commit can race the agent's next push. The agent then pulls and rebases as usual. If the restore loses the race, it stops, and the newer commit's own CI takes over.
- After a change here, `delivered` moves before delivery reaches the modules. A module CI run in that window sees drift: it restores the files it can reach, and is red once for workflow files.

## Layer 3: delivery

- `deliver.yml` in this repository is the only writer of owned files into modules (AD-6). It runs on every push to `main` here and hourly at minute 47. It can also be started by hand.
- Each run re-applies the full expected state, so it also repairs drift that the restore job skips.
- It pushes with a token minted from the org GitHub App, whose key never leaves this repository.

## Not used

- Rulesets with required status checks, because they block direct pushes. Existing ones are cut back during onboarding (AD-21):
  - On `main`, rulesets block only deletion and force-push.
  - On `v*` tags, rulesets block only update and deletion.
- CODEOWNERS, required review, and the required-reviewer rule, because agents can bypass review.
- Copilot coding agent's "Approve and run workflows" gate. It is on by default and is not part of this design.

## Custom-action deny list (guard lint)

Custom actions must not contain any of these:
- `actions/checkout`
- `actions/setup-dotnet`
- `actions/cache`
- `dapr init`
- a solution-wide `dotnet build` or `dotnet test`
- `nuget push`
- a registry login
- semantic-release

The list is maintained by hand, and occasional false positives are accepted.

## Nightly duplicate scan (this repository)

- A copy-paste detector, `jscpd`, scans every module's custom actions and the scripts they call. It covers YAML, shell, PowerShell, and Python. It reads each module's current `main`, never this repository's submodule checkouts.
- It runs inside `nightly.yml`. A fragment found in two or more modules fails the nightly run and names the code to move. It never blocks the Builds bump.
- The detection threshold needs tuning. Expect early noise from the Python tooling in Memories and Tenants until the gate rule removes it.
- The scan misses the same logic written differently. Agent review covers that, but runs only when a new custom action is enabled or the scan flags something.

## Hoisting shared code

Hoisting is an ordinary change made by an agent in this repository:
1. Move the code into Builds, as a shared stage or action.
2. Switch the modules over to it.
3. Delete the copies.

## Agent instructions

- Delivery writes one marked block, between `<!-- hexalith-cicd:begin -->` and `<!-- hexalith-cicd:end -->`, into each module's `AGENTS.md`, `CLAUDE.md`, and `.github/copilot-instructions.md`. Its text lives in this repository's templates. The guard checks it, and the restore job repairs it. The block says:
  - CI/CD is owned by Hexalith.CiCd.
  - Don't edit workflows, CI config, or the Builds pointer.
  - When CI fails, fix the product.
  - When CI itself is wrong, report it rather than work around it.
- `Hexalith.AI.Tools/hexalith-llm-instructions.md` links to the block and drops the line that says releases happen on merge.
- The `bmad-testarch-ci` skill ("Scaffold CI/CD quality pipeline"), installed in 14 modules, is a must-be-absent path. Delivery deletes it, and the guard flags it if it comes back.

## Claude Code deny rules

- Each module's `.claude/settings.json` gets `permissions.deny` entries for the owned paths, such as `Edit(/.github/workflows/**)`.
- The file exists in 15 modules, in 12 different versions. The entries are merged in, and every other key, including the allow list, stays module-owned.
- These rules never go in machine-wide managed settings: no allow rule can override a deny, so agents here couldn't edit Builds.
- For agents other than Claude Code, the rules are only instructions. Layers 1 to 3 are the real enforcement.
