# Nightly releases

`nightly.yml` runs at **02:17 UTC** and accepts manual dispatches on `main`.
The `nightly` concurrency group queues main runs without cancelling the active
run; as with any GitHub concurrency group, a newer queued run replaces an older
pending one. Skipped non-main dispatches use a separate group.
It executes `dispatch → wait → publish-ready → bump → bump-push → delivery-wait
→ keepalive`. Release dispatch, release wait, publication and delivery observation
use `cicd-app`. The bump producer uses only a read-only job token. The writer and
keepalive use their own job tokens. There are no push or pull request triggers.

Dispatch waits up to 45 minutes to observe two complete idle scans of main
`deliver.yml` runs, with 60 seconds between scans. An active run or a change
during pagination restarts that count. The wait also respects the read token's
use deadline and leaves time to select and dispatch targets. A delivery can
still arrive after the final observation. If the barrier cannot be read or does
not clear, dispatch stops. Modules come exclusively from committed `setup/*.yml`
files. The workflow has 18 fixed target slots: at most 17 modules plus Builds.
A registry above that capacity fails initialization and nothing is dispatched.
A module without a `delivered/<Repo>` ref is reported as not adopted, with
verdict `skip`; a skipped module never turns the night red. With a
ref, its current anonymous main snapshot must contain a regular
`.github/hexalith-ci.json`, and both caller files must have the same bytes and
file modes as their delivered render. Immutable releases must be confirmed
enabled. Failed adoption, caller drift or an unreadable setting fails that
module without blocking healthy siblings. Builds is always a separate target,
dispatched through `builds-release.yml` without module inputs.

Every dispatch requests the API's exact created run identity. The controller
never guesses a latest run or retries an uncertain dispatch. Modules receive
their pinned `delivered-sha`; their release workflow decides its own kill
switch, green CI, security gates and release content.

Wait polls those exact repository, caller, main and workflow-dispatch
identities every 60 seconds. Its one five-hour deadline includes every polling
slice and mint overhead. Wait ignores same-name artifacts created before the
current attempt started. Each completed attempt must supply exactly one
`hexalith-release-outcome` artifact. It must be unexpired, identify the
correlated run and head, and contain only `outcome.json`. Wait checks the run
again after reading artifacts. If a rerun started during that read, polling
continues with the newer attempt. An unreadable confirmation leaves the target
eligible for another poll within the existing deadline. Complete-mode releases
may intentionally publish a SHA older than the dispatched run's head.

Successful `published`, `nothing` and `disabled` outcomes pass. A successful
`ready` outcome passes only after the App authenticates the original bot-marked
draft, producer run and artifact digest, captured base ancestry, unchanged body
and version tag; publishes the same draft with one PATCH; and verifies the
returned release and peeled tag. A nonsuccess run, failed or unreadable
outcome, unfinished run, failed eligibility, uncertain dispatch/publication or
missing orchestration state fails the night. Package and image publishing
stays in the target run; nightly never rebuilds or republishes their bytes.

Each App job mints its own tokens through the pinned mint action. Dispatch and
publication use one explicitly scoped token per target. The delivery barrier
uses Actions read on CiCd. A dispatch token has Actions write on its one target,
plus Administration read on a module for the immutable-release check. Wait uses
Actions read on only its dispatched repositories. A publication token has
Contents write, Workflows write and Actions read on its one target. Nine
possible wait slices last at most 40 minutes each and
share the aggregate deadline; the ninth keeps the five hours covered when one
slice's mint fails. Mint epochs are recorded before the mint action;
every authenticated operation reserves time before the 50-minute use limit.
Mint failure never falls back to an older token. `skip-token-revoke: true`
prevents the action's post-job revocation from using an aged token; unused
tokens expire after GitHub's normal one hour. These mints require the CiCd
App installation (`vars.HEXALITH_CICD_APP_CLIENT_ID` and
`secrets.HEXALITH_CICD_APP_PRIVATE_KEY`, available only to the `cicd-app`
environment) on CiCd, Builds and every adopted module, with installation
permissions covering Actions read/write, Administration read, Contents write and
Workflows write. A missing installation or permission fails only the affected
mint and its target. `cicd-app` must let `main` runs, including scheduled ones,
start without reviewer approval; otherwise the jobs wait instead of running
unattended. Job limits are 105 minutes for dispatch, 330 for wait and 55 for
publication. The dispatch and publication controllers stop scheduling work
after 95 and 46 minutes respectively, leaving checkout, mint, finalization and
upload reserve. No cache, module checkout or
module code runs in an App job.

The token-free phase artifacts are `hexalith-nightly-dispatch-<attempt>`
(`dispatch.json`), `hexalith-nightly-wait-<attempt>` (`wait.json`) and
`hexalith-nightly-nightly-<attempt>` (`nightly.json`). They are kept for 90 days.
Upstream artifact IDs are carried through job outputs; downloads authenticate
the current nightly run, attempt, source, phase, registry and exact JSON member.
ZIPs are bounded and read in memory. Tokens and keys never enter these files.
Missing outputs or downloads produce explicit orchestration failures.
Dispatch, wait and publish-ready use their existing job token for the Builds
release and tag REST checks during initialization. Git object fetches are
credential-free and must match the verified tag and source identities.
Terminal JSON API request failures retain bounded, credential-redacted response
messages, request IDs, rate-limit/required-permission headers, attempt counts
and anonymous/scoped authentication context. Clipped fields and unreadable
response bodies are identified; response-message URLs are omitted. Artifact
download failures retain their existing diagnostics. A bare historical HTTP 403 cannot
establish a permission refusal: rate-limit and response evidence are required.
Diagnostic response reads have a two-second whole-operation limit and never
change retries, credentials or release verification.
Each job seeds a conservative failure document before checkout, outside its
cleanup directory, so unavailable controllers still leave a failed artifact
and summary. Normal initialization replaces that seed with the committed
registry and available observations.

The separate Evidence workflow checks pull requests and eligible pushes to
`main`. Nightly's pre-dispatch and post-bump checks observe Delivery.
GitHub suppresses push workflows for job-token writes. The nightly bump can
update only the Builds pin and existing rendered files, and keepalive is an
empty commit.

Open the nightly Actions summary for every target's verdict and available run
link, or download `nightly.json` for the same observations and short reasons.
Release details remain in those target runs. Upstream failure still permits
the later jobs to collect results and finalize reports. Explicit cancellation
stops new mints, dispatches and publication; finalization and upload may still
run with observations already available. A fresh manual dispatch, or re-running
all jobs, dispatches a new set of exact runs; target release workflows retain
responsibility for safely completing their original drafts. Re-running only
failed jobs is unsupported: GitHub reuses earlier attempts' job outputs, which
the attempt-bound handoff refuses, so a rerun of a failed wait or
publish-ready job fails closed without publishing. The dispatch job is red
whenever any target failed eligibility or dispatch; re-running failed jobs then
re-runs dispatch and its dependents, which dispatches a fresh set of exact runs
just like re-running all jobs. Unverified pre-existing publication is never
treated as proof that this nightly published a ready result.

Once nightly has run, hourly delivery's existing freshness check fails if the
last main nightly run is older than 26 hours. The bump waits for
`publish-ready` to finish, even if publication fails. Keepalive continues
after ordinary failures. A failed nightly job makes the overall night fail.
Explicit cancellation stops new work.

The duplicate scan runs independently at **03:07 UTC** or by manual
dispatch on `main`. It reports its own verdict in Actions. Successful uploads
retain `report.json` and `summary.md` for 90 days in
`hexalith-nightly-scan-<attempt>`. See the [duplicate scan runbook](duplicate-scan.md).

## Testing on demand

Dispatch `nightly.yml` on `main` to test the nightly without waiting for 02:17
UTC; it runs the same jobs and really releases, publishes and bumps. First
confirm that no `nightly.yml` run is queued or in progress, and plan no CiCd
push for 45 minutes, which is the dispatch barrier. Only the maintainer or an
interactive CiCd session dispatches; a module agent cannot. A run takes about an
hour. Judge it with
`python3 tools/nightly_acceptance.py --run <id> --module <Repo>`: each module's
verdict includes eligibility, the exact release run, CodeQL, any required
post-bump delivery, and duplicate scan coverage for the dispatch commit. For a
historical attempt with a scan job, the reader authenticates that attempt's
artifact. For an on-demand scan, start it after Nightly starts while the live
module heads still match the dispatch SHAs. The reader checks up to 100 completed
`scan.yml` runs on `main` created at or after Nightly started. A longer or
incomplete listing leaves coverage unproven. The current attempt of the first
qualifying run, ordered by creation time and run ID, decides coverage for each
module with an exact dispatch-commit row. An absent or stale row leaves
coverage unproven. A failing row, a run-level error in the selected report, or
a duplicate involving the module fails acceptance even if a later scan is
clean. Findings confined to other modules can fail the scan run while this
module passes acceptance. Scan coverage can be pending after a successful
Nightly run. `--checkpoint pilot` also checks the bump and keepalive.
Dispatching Nightly again without a fix only reports nothing to release.

`--receipt <path>` writes the identity-only receipt, and the tool exits 0 when
every named module passes, 1 when any fails, and 2 when the run is rejected or
unreadable. Alongside the compact receipt, record each module's dispatch SHA,
the deciding scan run and attempt, and the artifact name, ID and SHA-256 digest.

## Builds bumps and rollback

The producer fetches current CiCd `main`, independently of the scheduler SHA,
and selects the numerically newest stable `vX.Y.Z` in `builds-version`'s major.
It excludes `builds-skip`. Every acceptable release must be published, immutable,
authored by `github-actions[bot]`, agree with the remote and locally peeled tag,
and be ancestral to current Builds `main`. Incomplete release or tag evidence
fails the bump. A different major requires an explicit maintainer change.

To roll back, restore `builds-version`, add the bad newer tag to `builds-skip`,
re-render and commit the pin, policy and output together. `builds-skip` contains
one exact stable tag per line, for example:

```text
v5.2.0
v5.3.1
```

Empty lines are ignored. Whitespace-only lines, comments, ranges and malformed
tags are rejected with their line number. An absent skip file is treated as an
empty policy, so deleting it re-admits every previously skipped tag. With no
newer acceptable unskipped release, the producer
reports a successful no-change and no push, dispatch or propagation wait occurs.
No acceptable release is a verification failure.

The UTC creation date of the nightly run is its stable night key, including
reruns that cross midnight. A successful automatic bump records
`hexalith-nightly-bump: YYYY-MM-DD` in the body below the exact subject
`build(cicd): bump Builds to vX.Y.Z`. A reachable matching automatic bump on main
makes all later runs for that night no-change. A following UTC night may bump
again. Unreadable history fails this guard.

The producer renders in a disposable live-main checkout, locally commits the
candidate, and runs the shared global gate with the pin-dependent tool suites.
Only a successful candidate exposes `candidate.json` in
`hexalith-nightly-bump-<attempt>`. The separate
`hexalith-nightly-bump-report-<attempt>` (`bump.json`) records candidate, no-change
or failure observations. The isolated stdlib writer authenticates
the artifact's run, attempt, source, name and digest; reconstructs and hashes its
Git objects without executing them; and independently rechecks main, release,
tag, schema and night evidence. It allows only `builds-version` and existing
regular rendered files with the exact tag/commit substitution, plus newly
introduced CI JSON keys justified by the selected tagged schema's defaults.
It rejects unrelated edits, path additions/removals, mode changes and symlinks.
A main or eligible-release race fails the night without rebasing or retrying an
uncertain push. The push is an ordinary fast-forward of the exact validated
commit.

The default transport is the writer job's `GITHUB_TOKEN`, scoped to Contents and
Actions write. After confirmed push it explicitly dispatches `deliver.yml` on
main because token push events do not create downstream workflow runs. The
manual **qualify-bump** input runs only an isolated inert rendered-workflow
probe on main. It skips releases, production bump, delivery and keepalive.
It must record the remote SHA/tree and remove its probe refs. Hosted evidence
and the conditional App fallback are tracked in
[`nightly-bump-qualification.md`](nightly-bump-qualification.md). Fixture success
alone does not qualify the hosted transport. A definite nested-path Workflows
permission rejection selects a fresh CiCd-only Contents/Workflows write App
mint in `cicd-app`, the same verifier, and no explicit delivery dispatch; its
push trigger starts delivery. Other authorization or transport failures leave
qualification incomplete.

## Propagation and schedule keepalive

A confirmed push starts one aggregate 90-minute delivery and module-CI wait,
even when its subsequent explicit dispatch or report upload failed. The writer
job's failure remains red while observation collects available propagation links.
It polls every 60 seconds. The observer accepts only noncancelled main
`deliver.yml` runs on the bump commit or a proven descendant whose current
attempt actually started its `deliver` job. It selects the earliest qualifying
creation time, then run ID, and authenticates the sole current-attempt
`hexalith-delivery` report before reading its actual pushed module commits,
including repair pushes after skipped advancement. The report never authorizes
a repository: authorization comes from the bumped-main registry and valid
ancestral `delivered/<Repo>` refs, capped at 17 modules and excluding Builds.

For every pushed module commit, the first completed noncancelled main `ci.yml`
run on that commit or a proven descendant decides, ordered by completion time
then run ID. Only success passes; a later green result cannot hide a selected
red result. Delivery failure, a missing or invalid report, a skipped deliver
job, missing module CI or aggregate timeout fails the observation job. Sibling
links and diagnostics survive earlier failures in
`hexalith-nightly-delivery-wait-<attempt>` (`report.json`). Four possible App
mint/poll slices each last at most 40 minutes and share the same deadline, so a
failed mint cannot extend it or reuse an old credential. These tokens have
Actions read on exactly CiCd and the independently authorized module union.
No rendering, tests, linting or artifact code runs in this App job.

Keepalive runs even after failed or skipped ordinary prerequisites. It attempts
`nightly.yml`, `deliver.yml` and `scan.yml` enable calls independently, accepting the
API's empty HTTP 204 response. It fetches fresh main and uses its UTC committer
timestamp. Only a tip older than 50 days receives an empty
`build(cicd): keepalive` commit with that exact tip as parent; it never overwrites
a racing main. Enable and push failures remain red and are recorded in
`hexalith-nightly-keepalive-<attempt>` (`keepalive.json`). The enable API is the
primary protection against GitHub's 60-day schedule disable; the empty commit
is secondary. If Nightly stops and workflows become disabled, the maintainer
must re-enable them.

New job limits are 55 minutes for bump, 55 for bump-push, 105 for propagation and
15 for keepalive. Dispatch, release wait and publication use 105/330/55 minutes. Every App
mint belongs to its job, records its epoch before the action starts, reserves
time before the 50-minute use boundary and uses `skip-token-revoke: true`.
No token is carried through reports or artifacts. Push/qualification observations
are in `hexalith-nightly-bump-push-<attempt>` (`bump-push.json`); available links
also appear in the Actions summary. Missing producer outputs are failures or
skipped downstream jobs, never inferred to mean no-change.
