# Enforcement

How CI/CD changes made outside this repository are blocked and undone, and how custom actions are kept module-specific. Serves CAP-7, 8, 9, 11, and 14. The mechanics are in the architecture spine (AD-4, AD-6 to AD-8, AD-14).

## Layer 1: token scoping

- Module agents use a fine-grained token, limited to the module repositories, as their git and `gh` credential. It has Contents and Pull requests write access, and no Workflows, Administration, Actions, Variables, or Secrets write access. So GitHub rejects any push that touches `.github/workflows/**`, and any workflow dispatch. Module agents start each branch from the current `main`.
- Agents working in this repository use a second token, scoped to Builds and this repository only, in interactive sessions.
- Agent sessions never run with the maintainer's personal `gh` login, which has the `workflow` scope.
- Credentials that write are held in two GitHub environments, each usable from `main` only, with no required reviewers and no wait timer:
  - `cicd-app`, in this repository: the App key and client ID. It is used only by the delivery job and nightly's App jobs.
  - `hexalith-release`, in each managed repository: that module's own Zot push identity, which can push only that module's images and is distinct from the legacy `HEXALITH_ZOT_*`. The module's nuget.org Trusted Publishing policy names this environment and is scoped to the module's package-ID prefix.
- The caller's `publish` job grants `contents: write`, `actions: read` and `id-token: write`, and passes the NuGet user and registry push pair explicitly to the remote composite. NuGet/login runs inside that composite under the caller's policy; no public caller-key fallback input is needed. The job consumes only authenticated original artifact bytes and trusted action-path scripts, never a repository checkout or source build. Conflicting image tags fail before writes and all copied graph digests are checked. Skopeo 1.22.3 is version/image-digest/source-commit pinned (AD-11, AD-17; story 3-1).
- No `attestations: write` grant or signed build-provenance action is added: a publisher's current-run attestation cannot establish the original build on later completion/replay. Neither an artifact inventory nor OCI labels is treated as signed provenance (AD-17; story 3-1).
- Limits:
  - This layer doesn't cover owned files outside `.github/workflows/`. Layer 2 covers them.
  - `claude`, `cursor`, and `semgrep-app` are installed on no managed repository. `chatgpt-codex-connector` is installed only on the modules that use it, never on this repository or Builds. There it holds Workflows write access that the org can't remove, and it can publish its own module through an edited workflow on `main`. This is accepted, limited to that module by the per-module publish credentials. Only layers 2 and 3 and nightly's pre-dispatch check cover it.

## Layer 2: the guard

The guard is owned by Builds. It runs first in every CI run and takes seconds.

1. It reads the module's expected owned state from that module's own branch in this repository, `delivered/<Repo>`, by shallow sparse git clone. This repository is public, so no token is needed.
   - Delivery advances the branch only when the module passes its own checks, so it holds that module's last accepted render. A skipped module keeps its previous branch.
   - A ruleset on `delivered/**` restricts creation, updates, and deletion and blocks force-push. The App is its only bypass actor, so only delivery moves these branches.
   - A missing branch or perimeter fails the guard.
2. It compares the module with the expected state (perimeter in SPEC Constraints, entry kinds in AD-4). It also checks that:
   - every enabled hook and job action exists;
   - every custom action (`action.yml` or `action.yaml` under `.github/actions/**`) is composite. Each `uses:` names another directory under `.github/actions/`, or a third-party action at a full commit SHA, never Builds. Each action avoids the deny list below;
   - no module file waives or bypasses the release audit. This covers every MSBuild project file whatever its extension, plus `*.rsp` and NuGet config files. The lint rejects `NoWarn` for NU1900, NU1903, NU1904, or NU1905, `NuGetAuditSuppress`, `MSBuildWarningsAsMessages`, `TreatAsLocalProperty` on a `NuGetAudit*` property, and `auditSources`. It also rejects the test-filter properties `TestingPlatformCommandLineArguments` and `VSTestTestCaseFilter`;
   - commit messages pass commitlint, which also rejects `[skip ci]`-family markers and `skip-checks` trailers.
3. **On a PR:** it fails with the diff and the message "CI/CD is owned by Hexalith.CiCd. Fix the product code, not the pipeline." Module CI runs on pushes to `main` only, so branch pushes aren't judged.
4. **On a push to `main`:** it fails the same way. A separate restore job then:
   - runs only Builds code at the workflow's own commit, and recomputes the expected state from `delivered/<Repo>`, taking nothing from the CI job except its drift flag;
   - writes the expected state in one commit, skipping `.github/workflows/**`, which `GITHUB_TOKEN` can't write;
   - also skips the Builds gitlink and its `.gitmodules` section while the delivered Builds tag differs from the tag of the running workflow, so restore never splits the lockstep set. It writes `hexalith-ci.json` only when the tags match and the module's workflows already equal the delivered render;
   - dispatches CI on `main`, so the restored files are tested right away.

   What restore skips waits for the next delivery, at most one hour later. Every delivery run re-applies every delivered module.
5. **On `workflow_dispatch`:** it checks, and never restores.

It restores the files instead of running `git revert`, because an agent's commit usually mixes product changes with the CI/CD edit.

The release re-runs the same check on its release SHA, so a drifted caller can't ship.

Known effects:
- A module whose workflow files were edited stays red until the next delivery, within an hour.
- The restore commit can race the agent's next push. The agent then pulls and rebases as usual. If the restore loses the race, it stops, and the newer commit's own CI takes over.
- After a change here, a module's `delivered/<Repo>` moves before delivery reaches the module. A module CI run in that window sees drift: it restores the files it can reach, and is red once for workflow files.

## Layer 3: delivery

- `deliver.yml` in this repository is the only writer of owned files into modules (AD-6). It runs on every push to `main` here and hourly at minute 47. It can also be started by hand. Its runs on `main` are never cancelled.
- Each run first advances `delivered/<Repo>` for every module that passes all its checks. A branch only moves forward. A module whose branch would move backwards is reported as "superseded by `<sha>`".
- It then re-applies the render at `delivered/<Repo>` to every module that has the branch, passing or not, so it also repairs drift that the restore job skips. When the global checks fail, it advances nothing but still re-applies.
- Before using Builds at a branch's `builds-version`, it confirms that the tag is acceptable (SPEC Constraints).
- It pushes with a token minted from the org GitHub App, whose key never leaves this repository's `cicd-app` environment.
- Nightly's pre-dispatch check adds one more repair point. A module whose live `ci.yml` or `release.yml` differs from `delivered/<Repo>` is not released, and the nightly run fails.

## Not used

- Rulesets with required status checks, because they block direct pushes. During onboarding, rulesets are set to exactly these, created where missing and cut back where stricter (AD-21):
  - On `main`, rulesets block only deletion and force-push.
  - On `v*` tags, rulesets block only update and deletion. Leftover drafts and tags are deleted before the tag ruleset is set. An orphan tag found later is deleted with the ruleset briefly disabled.
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

- A copy-paste detector, `jscpd`, scans every module's custom actions and the scripts they call. It covers YAML, shell, PowerShell, and Python. It reads each module's current `main`, never this repository's submodule checkouts. It uses this repository's committed config, never one from the scanned module.
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
  - Run `python3 references/Hexalith.Builds/check.py` before you push.
  - Don't write tests that assert workflow YAML, and don't use skip markers such as `[skip ci]`.
- `Hexalith.AI.Tools/hexalith-llm-instructions.md` links to the block and drops the line that says releases happen on merge.
- The `bmad-testarch-ci` skill ("Scaffold CI/CD quality pipeline"), installed in 14 modules, is a must-be-absent path. Delivery deletes it, and the guard flags it if it comes back.

## Claude Code deny rules

- Each module's `.claude/settings.json` gets `permissions.deny` entries for the owned paths, such as `Edit(/.github/workflows/**)`.
- The file exists in 15 modules, in 12 different versions. The entries are merged in, and every other key, including the allow list, stays module-owned.
- These rules never go in machine-wide managed settings: no allow rule can override a deny, so agents here couldn't edit Builds.
- For agents other than Claude Code, the rules are only instructions. Layers 1 to 3 are the real enforcement.

## Accepted residuals

These gaps are known and accepted under the careless-agent model:
- Org owners and agents in this repository can reach the App key through a push to `main`.
- Builds `v*` tag creation stays unrestricted, but a hand-made tag reaches no module: modules take a tag only if its release is published, immutable and authored by `github-actions[bot]`, and its commit is an ancestor of Builds' `main` (SPEC Constraints, acceptable tag). The Builds `v*` ruleset blocks only update and deletion. A ruleset can't restrict creation to GitHub Actions and the App, because GitHub doesn't accept GitHub Actions as a bypass actor. Story 1's probe on CiCd, 2026-11-08:
  - Without a bypass, a creation rule on `probe-*` refused `GITHUB_TOKEN` both through REST `POST git/refs` (422) and through `git push` (GH013). This was run 42526410704.
  - Adding `Integration` 15368 (GitHub Actions) as a bypass actor was rejected with 422: "Actor GitHub Actions integration must be part of the ruleset source or owner organization".
  - An installed App is accepted as a bypass actor (CiCd's `delivered/**` ruleset). Restricting `v*` creation would therefore mean the release creates tags with an App token instead of `GITHUB_TOKEN`, which the spine doesn't do.
- An obfuscated `NoWarn`, or an MSBuild import through a computed path, escapes the text-based audit lint.
- Completing a draft doesn't re-run the audit.
- The registry pull pair is readable by every CI step and by Dependabot runs.
- Custom-action SHA pins are checked by their text only.
- `chatgpt-codex-connector` can publish its own module (Layer 1).
- A module whose last CI run on `main` is older than the 90-day retention fails "main is red" until its next commit. Bumps arrive nearly every night.
