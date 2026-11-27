# Story 20 — Read-Only AD-21 Preflight & Maintainer Handoff Checklist (2026-11-27)

Recorded `2026-11-27` under **Admin Option 1** (read-only GitHub API inspection only; zero org/repo admin mutations, zero pushes, zero remote writes, zero secret values printed).

## Source, Tree, Blob & Profile Identities

| Item | Commit / Tag / Blob / Tree Identity |
| --- | --- |
| CiCd baseline `HEAD` | commit `3a8a088942347709ffe626b340879cd3fb21e89e`, tree `fb5316ca546f15a42a1486f4593f368361e72408` |
| CiCd `builds-version` blob | `c76a5987ef9c9702eefa014a153509015dba735b` (`v6.9.1`) |
| CiCd `tools/{render,validate,check_global}.py` blobs | `8e0959e358376d141183ef0c7f4fd259abf63a11`, `f69476ee4b6c1f9b566bec17bdee8fd1689b1579`, `39ed2f6c802e286622e09b37a76757fae09ea65f` |
| Builds `v6.9.1` release | tag/commit `91cb7cba990ffdf82930f9bf8cb68aef41baba76`, tree `83bf776a4ae75d3302b77fb57efdf53cfe490432` (published, immutable, authored by `github-actions[bot]`) |
| EventStore live `origin/main` | commit `0a224fb7536472439b6647e282061f2a3a352c71`, tree `ff28113a9648a5cbf0b99640dba333e8edfbf360` |
| EventStore committed CiCd gitlink | commit `5484fae6c284cd8fe70b51bf921c5b31509b6c27`, tree `9acbfb3b482592e89b23c68a2fdb67bc62afc981` |
| Refreshed `evidence/20/planned-registration.yml` | blob `0e2cd81ea1c14c1c4adc26f5de66111f7213e79a`, SHA-256 `f0256b56a5bdf9913ab324562e43e06f9d162db999f3c9c01aca390a0d0d975b` |
| Accepted adoption ref `delivered/Hexalith.EventStore` | `HTTP 404` (`Not Found` — unadopted) |
| CiCd-agent profile | `/home/administrator/.config/gh-cicd-agent` (`login: jpiquot`, no inherited `GH_TOKEN`/`GITHUB_TOKEN`) |
| Maintainer read-only profile | `/home/administrator/.config/gh` (command-local override only; `login: jpiquot`) |
| Read-only preflight capture digest | SHA-256 `2ee1925bb760d5394eac9a5667675baefd9659e47920ae64f5b550e7c9874ac1` (20 endpoints, exit 0 except expected 404 on `delivered/Hexalith.EventStore`) |

## Live AD-21 Preflight Status (`Hexalith/Hexalith.EventStore`)

| AD-21 Precondition | Current Live State | Verdict |
| --- | --- | --- |
| Default branch | `main` | Pass |
| `hexalith-cicd` App installation (`id=179966090`) | `repository_selection: all`, permissions `actions:write, contents:write, metadata:read, workflows:write, administration:read, security_events:read` | Pass |
| Secret scanning & push protection | Both `enabled` | Pass |
| Actions artifact & log retention | `90` days (maximum `90`) | Pass |
| Code scanning default setup | `not-configured` | Pass |
| Dependabot security updates (`automated-security-fixes`) | `enabled: false` | Pass |
| Unmarked draft releases | `0` drafts across latest `100` releases (latest published tag `v5.6.0`) | Pass |
| Immutable releases | `enabled: false` (must remain disabled until immediately after adoption) | Pass (pre-adoption) |
| **Repository & inherited rulesets (`rulesets?includes_parents=true`)** | Returns **2** repository-level rulesets (`source_type: "Repository"`) and **0** organization-level inherited rulesets: `14479516` ("Protect" on `~DEFAULT_BRANCH` with PR + 8 legacy status checks + 2 user bypass actors) and `26299155` ("Protect finite Parties SDK 3.130.2" on `refs/heads/release/parties-sdk-3.130.2`); **missing** `refs/tags/v*` tag ruleset | **BLOCKING** |
| **`hexalith-release` environment** | Absent (only `copilot` and `production` exist) | **BLOCKING** |
| **Org Actions variable `HEXALITH_NUGET_USER`** | `10` selected repos; `Hexalith.EventStore` **absent** | **BLOCKING** |
| **Org Actions secrets `HEXALITH_REGISTRY_PULL_USERNAME` / `_PASSWORD`** | `10` selected repos; `Hexalith.EventStore` **absent** | **BLOCKING** |
| **Org Dependabot secrets `HEXALITH_REGISTRY_PULL_USERNAME` / `_PASSWORD`** | `10` selected repos; `Hexalith.EventStore` **absent** | **BLOCKING** |
| **Repo variable `HEXALITH_RELEASE_PUBLISH_ENABLED`** | Currently `"true"` (updated `2026-11-17T10:20:15Z`) | **ACTION REQUIRED** (set `"false"` during cutover per `docs/ordered-module-adoption.md`, then re-enable under explicit maintainer authorization before CAP-16 nightly acceptance) |
| **NuGet.org trusted publishing policy** | External to GitHub API; unverified | **ACTION REQUIRED** (maintainer verification/creation) |
| **Org App `chatgpt-codex-connector` (`id=77847816`)** | `repository_selection: all` with `contents:write, workflows:write` | **ACTION REQUIRED** (restrict per AD-7/AD-21 so it only accesses modules where it is explicitly used) |
| **Org App `cursor` (`id=182926560`)** | `repository_selection: selected` with `contents:write, workflows:write` (repo list inaccessible via API) | **VERIFY** in GitHub org UI that `Hexalith.EventStore` is excluded per AD-7/AD-21 |
| **Azure private runner / approval env / authority & custody** | Absent (`payload-protection-azure-conformance` absent) | **DEFERRED POST-MVP** (2026-11-17 human decision) |

### Ruleset Contract Distinction (`deliver.py:app_checks` vs AD-21 Policy)

- **`deliver.py:app_checks` (lines 41–68)** inspects `rulesets?includes_parents=true` and enforces: `enforcement == "active"`, exact `conditions == {"ref_name": {"include": [...], "exclude": []}}`, parameterless rule entries, and exact rule-target set `{("branch", ("refs/heads/main",), ("deletion", "non_fast_forward")), ("tag", ("refs/tags/v*",), ("deletion", "update"))}`. Any extra active ruleset (such as `26299155`) or extra rule fails `app_checks`. `deliver.py:app_checks` does not inspect `bypass_actors`.
- **AD-21 policy** additionally sets `bypass_actors: []` on both rulesets, matching already-adopted `Hexalith.Commons` and `Hexalith.Works`:
  - Branch ruleset `"Protect main"`: `target: "branch"`, `enforcement: "active"`, `conditions: {"ref_name": {"include": ["refs/heads/main"], "exclude": []}}`, `rules: [{"type": "deletion"}, {"type": "non_fast_forward"}]`, `bypass_actors: []`.
  - Tag ruleset `"v tags"`: `target: "tag"`, `enforcement: "active"`, `conditions: {"ref_name": {"include": ["refs/tags/v*"], "exclude": []}}`, `rules: [{"type": "update"}, {"type": "deletion"}]`, `bypass_actors: []`.

## Exact Maintainer Handoff Checklist (AD-21 Order)

### Phase 1 — Before CiCd Registration Push / Delivery Adoption

1. **Resolve product & contract blockers first** (see `continuation-audit-2026-11-27.md`):
   - Decide `.NET 10.0.402` SDK / `net10.0` runtime handling for `PublishedCompatibility.Tests` (`v3.128.2` tagged source) and `tools/folded-snapshot-compatibility/run.sh`, since Builds `v6.9.1` and `tools/render.py` restrict `additionalSdkVersion` to `11.0.xxx`.
   - Resolve the 32 un-waivable `tools/scan.py` coverage errors on EventStore `origin/main` (13 in `scripts/run-with-temp.sh`, 14 in `tools/folded-snapshot-compatibility/run.sh`, and the unauthorized `references/Hexalith.Builds` import inside `scripts/ci-product-checks.py:commitlint_fixture_environment()`), preserving signed locked commitlint provisioning, and record human review decisions for any remaining located Python coverage gaps in `tools/scan-coverage-gaps.json`.
   - Audit `tests.failSkips` (51 existing skips), `tests.minimumExpectedTests`, and CodeQL (`codeql-config.yml` `_bmad-output/**` ignore, shared timeout budget, and `Admin.UI/wwwroot/js/{download,interop}.js` JS coverage disposition).
   - **Pre-adoption verifier prerequisite:** Before any further pre-adoption EventStore product pushes, refresh `tools/qualification/pre-adoption/eventstore/pre-adoption-verify.py` (whose `PREPARATION_PATHS` allowlist currently excludes `scripts/run-with-temp.sh` and new Python test paths) and `tools/qualification/pre-adoption/eventstore/fixtures/planned-configuration.json` (which still carries stale `additionalSdkVersion: 10.0.404` and omits `aspire`, `releaseTimeoutMinutes`, and `nightlyTimeoutMinutes`). Only after that refresh passes on exact committed inputs may the module-agent push the EventStore product update.
2. **Set `HEXALITH_RELEASE_PUBLISH_ENABLED` to `false` during cutover** on `Hexalith/Hexalith.EventStore` (keep publication disabled during adoption per `docs/ordered-module-adoption.md`).
3. **Replace repository rulesets on `Hexalith/Hexalith.EventStore` to exact AD-21 state** (`rulesets?includes_parents=true` currently has 0 org rulesets and 2 repo rulesets):
   - Replace ruleset `14479516` ("Protect") so `main` has **only** `include: ["refs/heads/main"]`, `exclude: []`, rules `deletion` + `non_fast_forward`, and AD-21 `bypass_actors: []`.
   - Delete ruleset `26299155` ("Protect finite Parties SDK 3.130.2") once no longer required (any extra active ruleset fails `deliver.py:app_checks`).
   - Create active tag ruleset for `include: ["refs/tags/v*"]`, `exclude: []`, rules `update` + `deletion`, and AD-21 `bypass_actors: []`.
4. **Create environment `hexalith-release` on `Hexalith/Hexalith.EventStore`**:
   - Restrict deployment branch policy to `main` only.
   - Add environment secrets `HEXALITH_REGISTRY_USERNAME` and `HEXALITH_REGISTRY_PASSWORD` holding EventStore's own Zot push identity.
5. **Configure NuGet.org trusted publishing**:
   - Add a `nuget.org` trusted publishing policy for `Hexalith/Hexalith.EventStore`, workflow `release.yml`, environment `hexalith-release`, scoped to `Hexalith.EventStore*`, beside any existing legacy policy.
6. **Grant organization secrets & variables to `Hexalith.EventStore`**:
   - Add `Hexalith.EventStore` to Org Actions variable `HEXALITH_NUGET_USER`.
   - Add `Hexalith.EventStore` to Org Actions secrets `HEXALITH_REGISTRY_PULL_USERNAME` and `HEXALITH_REGISTRY_PULL_PASSWORD`.
   - Add `Hexalith.EventStore` to Org Dependabot secrets `HEXALITH_REGISTRY_PULL_USERNAME` and `HEXALITH_REGISTRY_PULL_PASSWORD`.
7. **Enforce AD-7/AD-21 GitHub App restrictions**:
   - **Restrict `chatgpt-codex-connector` (`id=77847816`)** from `repository_selection: all` (`contents:write, workflows:write`) to only the specific repositories where it is explicitly authorized under AD-7/AD-21.
   - **Verify `cursor` (`id=182926560`, `selected`)** excludes `Hexalith.EventStore` in the GitHub org App settings UI.
8. **Verify CodeQL state**: current analyses come from `.github/workflows/codeql.yml:analyze`, which delivery replaces; clear stale CodeQL configurations if any remain after adoption.

### Phase 2 — Registration, Delivery & Adopted CI

9. Copy the refreshed `evidence/20/planned-registration.yml` (after Phase 1 audits clear) to `setup/Hexalith.EventStore.yml`, render with `uv run --locked --script tools/render.py`, advance `references/Hexalith.EventStore` gitlink to the verified live `main` commit, commit together in one CiCd commit, verify locked `tools/check_global.py` + `tools/validate.py` (`--scope full`), and push to CiCd `main`.
10. Authenticate `deliver.yml` advancing `delivered/Hexalith.EventStore` and pushing one `build(cicd): apply ...` commit to EventStore `main` (replacing `.github/workflows/`, delivering `.github/hexalith-ci.json`, `.github/dependabot.yml`, `references/Hexalith.Builds` at `v6.9.1`, instruction blocks, and `.claude/settings.json` denies, and removing `.releaserc*` / `commitlint.config.*`).
11. Authenticate green adopted `ci.yml` on EventStore `main`, including retained offline Azure checks, `after-unit-tests`, stage 4 integration projects, and `after-integration-tests` (applicable on-premises Kubernetes/kind qualification).

### Phase 3 — Immediate Post-Adoption Cleanup, Release Authorization & Nightly Acceptance

12. **Immediately after accepted adoption (maintainer):**
    - Turn on `immutable-releases` on `Hexalith/Hexalith.EventStore`.
    - Delete legacy `nuget.org` publishing policies for EventStore.
    - Remove `Hexalith.EventStore` from legacy org secrets, remove its package IDs from the legacy `NUGET_API_KEY` scope, clean up legacy repo secrets (`HEXALITH_CI_REGISTRY_*`, `REGISTRY_*`, `NUGET_TRUSTED_PUBLISHING_USER` if unused), and revoke the legacy Zot push identity on EventStore repositories.
13. **Post-adoption module-agent cleanup (using normal `run-with-temp python3 references/Hexalith.Builds/check.py` — the pre-adoption exception has expired):**
    - Delete tool-only root `package.json`, `package-lock.json`, and `.husky/`.
    - Delete legacy release/governance tooling and fixtures no longer needed after adoption: `.github/codeql/codeql-config.yml` (if confirmed unnecessary under shared CodeQL), `tools/verify-release-candidate.mjs`, `tests/Hexalith.EventStore.Contracts.Tests/Packaging/Fixtures/semantic-release-github-success.mjs`.
    - Delete the 13 reintroduced legacy-workflow-coupled `tools/tests/*.py` files, `tools/tests/test_check_deferred_work.py`, `tools/tests/commitlint.test.mjs`, `tests/Hexalith.EventStore.Contracts.Tests/Packaging/DeferredWorkPathTests.cs`, and `tests/Hexalith.EventStore.Contracts.Tests/Packaging/SharedInstructionEntryPointTests.cs` (retire per `AGENTS.md` agent-tooling gate rule).
    - Update `docs/ci.md` to remove pre-adoption legacy references and trim `README.md` from 227 lines to `<=150` lines (`docs_check` `D-LENGTH`) before enabling `docs: fail`.
14. **Explicit maintainer publication authorization (required before CAP-16 nightly acceptance):**
    - Note that `HEXALITH_RELEASE_PUBLISH_ENABLED=false` yields release outcome `disabled`, which is a valid controller outcome but does **not** satisfy CAP-16 (`published` or `nothing`).
    - Under separate maintainer product-release authorization after adopted CI and post-adoption cleanup are green, flip `HEXALITH_RELEASE_PUBLISH_ENABLED` from `"false"` to `"true"` on `Hexalith/Hexalith.EventStore`.
15. **CAP-13 / CAP-16 Nightly Acceptance:**
    - Wait for or trigger an authorized central `nightly.yml` run on CiCd `main` with `qualify-bump: false`.
    - Run `tools/nightly_acceptance.py` and authenticate EventStore's own rows (eligibility, passing CodeQL, verified `published` or valid `nothing`, qualifying scan row, and any required post-bump delivery evidence).

### Deferred Post-MVP (2026-11-17 Human Clarification)

- Dedicated private runner group `payload-protection-azure-private-ephemeral`, approval environment `payload-protection-azure-conformance`, `PAYLOAD_AZURE_AUTHORITY_JSON` / `PAYLOAD_AZURE_CUSTODY_JSON` custody provisioning, and live Azure fault qualification are explicitly deferred post-MVP. Claim no Azure live pass.
