# Story 11 implementation readiness

This is an incomplete implementation checkpoint. No pilot has been adopted and
no delivery, release, branch probe or scheduled-night result is claimed.

## Initial prerequisites and live access, 2026-11-15

- Stories 10-1 and 10-2 are recorded `done`. The accepted three-result handoff
  and provisional Update branch prohibition remain unchanged. The meaningful
  operation still belongs after actual pilot delivery.
- `recheck-preflight.py`, `recheck-preflight.json` and
  `recheck-preflight.log` preserve the fresh authenticated GET checks. The
  inherited profile is `/home/administrator/.config/gh-cicd-agent`, with neither
  token override present. Administration uses only the command-local
  `/home/administrator/.config/gh` profile, account `jpiquot` (`6775094`).
- Both pilots still have no rulesets, only their legacy `production`
  environment and disabled immutable releases. The release kill switches are
  exactly `true`, retention is 90 days, code-scanning default setup is
  `not-configured`, Dependabot returns boolean `enabled: false`, and secret
  scanning push protection is enabled. Org pull-secret and NuGet-variable
  grants still name Builds alone. These are observations, not provisioning.
- The CiCd App installation metadata is readable, but its selected repositories
  remain unverified. `GET
  /user/installations/179966090/repositories?per_page=100` returns HTTP 403 under
  the intended maintainer profile: “You must authenticate with an access token
  authorized to a GitHub App, a personal access token, or basic auth in order to
  list repositories for an installation.” Account administrator metadata does
  not resolve that token access failure.
- The existing signed-in Windows Chrome session reaches
  <https://github.com/organizations/Hexalith/settings/installations/179966090>,
  then displays **Confirm access**, signed in as `@jpiquot`. GitHub requires
  human passkey/security-key, Mobile, authenticator or password authentication
  before installation settings are accessible. The browser is left on that
  page. `app-selection-browser-blocker.json` records the timestamped repeated
  read-only observation. No authentication bypass,
  App-key access or credential change occurred.
- AD-21 requires verified App selection first. No App-dependent administration
  or remote mutation was attempted while this prerequisite remained unverified.
  Rulesets, stale legacy release/tag cleanup, the main-only release environment,
  scoped Zot identities, scoped NuGet policies, org grants and later immediate
  credential cleanup remain outstanding.
- A separate prerequisite blocks product-preparation pushes: the exact required
  `python3 references/Hexalith.Builds/check.py` exits 2 in both pilot roots,
  because the nested Builds checkout is uninitialized and its script is absent.
  `pre-adoption-prepush-blocker.json` records both exact errors. Current shared
  `local_check.py` additionally requires an adopted `.github/hexalith-ci.json`,
  which neither pilot has. No nested initialization or owned-file bootstrap was
  used to bypass either requirement. The successful disposable product checks
  are independent evidence; they do not satisfy the mandated pre-push command.

## Exact source revisions

| Repository | Source revision |
| --- | --- |
| CiCd baseline | `37e73a99dfe82c3b7741554d6f4ff2207711644b` |
| Builds source | `73e60af8a1fcdf3f06726d5d1b6e1199cce778ee` |
| Commons current main | `ab5e92faa3bab1fa43b8ecadd423432dfe652bb2` |
| PolymorphicSerializations current main | `476cfccac3c5ba694a8e0ef11b1157728b9ec093` |

`module-fetch.log` records successful protected-module-token fetches. Local
pilot checkouts were fast-forwarded to those remote mains, preserving the
intervening manifest/lock changes and Poly README change. No product branch,
probe ref/PR, commit or push was created. No nested submodule was initialized.

## Completed local changes

- Delivery accepts a strictly boolean disabled security-update response or
  the legacy 404 after the successful Administration-protected preflight.
  Successful JSON `null` is rejected by the API transport for these
  absence-enabled reads, keeping it distinct from an authenticated 404.
  Enabled, malformed, 401 and 403 responses fail
  their own module while healthy siblings continue.
- Builds' publisher reads the already authenticated package inventory from
  NuGet after pushes and before container publication/GitHub finalization.
  It reuses `release_draft.package_identity` for exact ID, version and source
  commit. It retries pending/indexing-delayed packages and transient transport
  responses with an overall 30-minute bound, bounded reads and 180 attempts;
  identity/source conflicts and authorization errors fail immediately. No feed
  request receives a publishing key or GitHub Authorization header.
- Commons has an `after-unit-tests` composite that packs the twelve explicit
  existing Release outputs with `--no-build --no-restore`, checks payloads and
  symbols, then compiles only its generated package consumer. Packing uses the
  CI package, audit-off, no-response-file and trusted NuGet-config flags. The
  consumer copies the unchanged module `global.json` and confines its package,
  HTTP and plugin caches plus CLI home to its cleaned temporary directory.
  The existing payload/symbol validator is retained unchanged.
- Both SDK `11.0.100`/MTP pins and all C# product test sources are unchanged.
  Duplicated legacy publication verifiers, manifests and npm files are retained
  until shared verification is released. No owned module file was edited.

## Verification

- `builds-publisher-python312.log`: all 17 publisher regressions passed on
  Python 3.12 in 23.628 seconds.
- `builds-publisher-python314.log`: all 17 passed on runner Python in 23.712
  seconds. Unit coverage includes generic inventories, missing packages,
  indexing delays/transient errors, wrong ID/version/source, authorization,
  size/deadline bounds and empty inventories. The actual composite additionally
  proves that missing/wrong-source/unauthorized NuGet reads produce a failed
  outcome with no GitHub publication or tag creation.
- `package-mode-verification.py` and `package-mode-python314.log`: disposable
  direct-repository exports built both pilots through the shared package-mode
  pipeline, then ran all nine C# suites: **357 Commons + 15 Poly = 372 passed,
  zero skipped**. Commons packed/validated all twelve payload/symbol package
  pairs and restored/built the isolated package-only consumer. The log records
  exported source revisions and SHA-256s of the exact Commons overlay files;
  final source hashes match those observations. Scratch was removed at exit.
- `deliver-python312.log`: all 20 delivery tests passed in 337.242 seconds.
  The null-response follow-up is recorded separately because that guard was
  added during this first suite run.
- `deliver-python314.log`: all 20 delivery tests passed on runner Python 3.14.4
  in 426.449 seconds, including the final null-response/sibling-isolation case.
- `deliver-null-python312.log`: the focused malformed/null/authorization test
  passed on Python 3.12 in 82.070 seconds, including every sibling-isolation
  subcase.
- `delivery-runtime-python312-initial.log` retains the first runtime failure:
  globally rejecting null responses removed the release identity from an
  existing malformed-ancestry diagnostic. The guard now rejects null only on
  the absence-enabled security-updates read; other consumers retain their
  existing response-shape validation and identity diagnostics. The final
  runtime checks cover that corrected null-versus-404 path directly.
- `delivery-runtime-python312.log` and `delivery-runtime-python314.log`: all
  twelve runtime tests pass on the final code in 15.038s and 13.119s. This
  includes the direct null-versus-404 check and original ancestry diagnostics.
- `render-check.log`: wrapped locked renderer `--check` exits 0 without any
  production registration or render/pin change.
- `final-local-checks.json`: preserved frozen intent/baseline, final source
  hashes, unchanged SDK/C# and owned module content, no production registration,
  unchanged default authentication, credential/private-key evidence scan and
  clean whitespace checks. Full committed adoption-candidate/global validation
  and live acceptance remain pending.

Additional final compatibility/runtime logs and source/evidence checks are
listed in the story's Verification section when complete.

## Resumed prerequisite check, 2026-11-16

`resume-prerequisites.py`, `resume-prerequisites.json` and
`resume-prerequisites.log` record a fresh read-only check. The intended
maintainer profile still receives HTTP 403 for the installation repository
inventory. Its readable account, repository identity, OAuth scope headers and
App permission metadata do not establish access to that inventory. The
existing Chrome window still displays **Confirm access** for `@jpiquot` at
the exact installation settings URL; no authentication control was invoked.
The inherited CiCd-agent profile and absent token overrides are unchanged.

Both exact module check commands again exit 2. Inspection of their common
legacy Builds gitlink, `9f5d751f7ab0b7a621dcd18b589bf061fabac6ec`, additionally
establishes that the pinned commit contains neither `check.py` nor
`Github/lib/local_check.py`. Initializing that checkout would not resolve the
missing command. The current checker's adopted configuration and delivered
state requirements also exclude a direct bootstrap. See
`pre-adoption-check-resolution.md` for the smallest decision scope and its
effect on the frozen pre-push requirement. No exception was assumed.

No new source change, remote mutation, production registration, module push,
shared release or adoption was performed. The existing source changes are
already verified locally; the remaining composite tasks depend on the
unmet prerequisites and remain open.

## Provisioning after human GitHub authentication

The human's subsequent **done** resolved the browser authentication boundary.
The active installed-App document initially showed exactly Builds and CiCd;
the stale Confirm access document remained elsewhere in the accessibility tree
and was not treated as the active page. Added only the two pilots, saved, then
reloaded and verified exactly four selected repositories. Completed AD-21's
legacy CodeQL/tag cleanup, exact protection rules, main-only release
environments and isolated registry identities/secret pairs. Existing access,
published releases/packages and main refs are preserved. See
`provisioning-status.md` for exact resources, results and verification limits.

NuGet policy creation is incomplete. The prepared Commons scoped policy
returned a generic creation error. Page refresh reached NuGet Sign In, and
ordinary Microsoft sign-in now requires the human's face/fingerprint/PIN or
security key. No credentials were entered; no new policy or duplicate-policy
restriction is proved. Both legacy policies remain. Later settings and org
grant writes are deferred to preserve AD-21 ordering. The separate pre-push
requirement remains unchanged; authentication does not approve its exception.

## Remaining execution

After the human completes the displayed Microsoft/NuGet authentication,
refresh the policy inventory, add both scoped policies beside their legacy
policies and complete the remaining AD-21 settings/grants in order. Resolve
the separate pre-adoption check decision before any module product push.
The source change still needs a
validated Builds commit and interactive shared release; wait for an acceptable
published immutable tag before removing either module's duplicated verification
or tool-only npm files. Publish the Commons product hook with the protected
module credential after resolving the pre-adoption check/bootstrap prerequisite
and passing the required command. Create the disposable product
probe/PR before adoption. Register/render both modules with the released Builds
pin and validate a committed candidate before pushing it. Authenticate both
actual delivery results, perform the immediate policy/credential cleanup, test
fresh-main branching and meaningful Update branch, clean all probes, and await
green pilot CI plus one real scheduled nightly. Fixtures and this checkpoint
cannot satisfy those live acceptance criteria.
