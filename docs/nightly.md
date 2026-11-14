# Nightly releases

`nightly.yml` runs at **02:17 UTC** and accepts manual dispatches on `main`.
The `nightly` concurrency group queues main runs without cancelling the active
run; as with any GitHub concurrency group, a newer queued run replaces an older
pending one. Skipped non-main dispatches use a separate group.
It executes `dispatch → wait → publish-ready`, each in the `cicd-app`
environment. There are no push or pull request triggers.

Dispatch waits up to 30 minutes for every main `deliver.yml` run to become
terminal. If that barrier cannot be read or does not clear, nothing is
dispatched. Modules come exclusively from committed `setup/*.yml` files. The
workflow has 18 fixed target slots: at most 17 modules plus Builds. A registry
above that capacity fails initialization and nothing is dispatched.
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
slice and mint overhead. A rerun attempt cannot consume an older attempt's
outcome. Complete-mode releases may intentionally publish a SHA older than
the dispatched run's head. Each completed run supplies its sole unexpired
`hexalith-release-outcome` artifact, containing only `outcome.json`.

Successful `published`, `nothing` and `disabled` outcomes pass. A successful
`ready` outcome passes only after the App authenticates the original bot-marked
draft, producer run and artifact digest, captured base ancestry, unchanged body
and version tag; publishes the same draft with one PATCH; and verifies the
returned release and peeled tag. A nonsuccess run, failed or unreadable
outcome, unfinished run, failed eligibility, uncertain dispatch/publication or
missing orchestration state fails the night. Package and image publishing
stays in the target run; nightly never rebuilds or republishes their bytes.

Each job mints its own App tokens through the pinned mint action. Dispatch and
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
unattended. Job limits are 55 minutes for
dispatch, 330 for wait and 55 for publication. Controllers in the 55-minute jobs
stop scheduling work after 46 minutes, leaving checkout, mint, finalization and
upload reserve. No cache, module checkout or
module code runs in an App job.

The token-free phase artifacts are `hexalith-nightly-dispatch-<attempt>`
(`dispatch.json`), `hexalith-nightly-wait-<attempt>` (`wait.json`) and
`hexalith-nightly-nightly-<attempt>` (`nightly.json`). They are kept for 90 days.
Upstream artifact IDs are carried through job outputs; downloads authenticate
the current nightly run, attempt, source, phase, registry and exact JSON member.
ZIPs are bounded and read in memory. Tokens and keys never enter these files.
Missing outputs or downloads produce explicit orchestration failures.
Each job seeds a conservative failure document before checkout, outside its
cleanup directory, so unavailable controllers still leave a failed artifact
and summary. Normal initialization replaces that seed with the committed
registry and available observations.

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
last main nightly run is older than 26 hours. This story stops at publication
and reporting. Story 9 inserts the secretless duplicate scan **after
`publish-ready` regardless of its result and before the bump**. The later bump
must continue regardless of publication or scan failure; no placeholder jobs
are present here.
