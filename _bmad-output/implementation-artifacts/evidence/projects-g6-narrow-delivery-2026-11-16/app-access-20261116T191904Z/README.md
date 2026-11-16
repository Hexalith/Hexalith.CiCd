# Authorized CiCd App access grant attempt — 2026-11-16

The user requested “give access”, authorizing the existing `hexalith-cicd` App
installation to gain only `Hexalith.Projects` repository access. This continuation
used the configured maintainer profile for installation administration only.

The environment variable `HEXALITH_CICD_APP_CLIENT_ID` identifies App
`Iv23liRwXrNRB9QVzmuh`, App ID `5671811`, installation `179966090`.
Projects repository ID is `871087402`. Authenticated account `jpiquot` is an active
Hexalith organization owner (`role: admin`) and has Projects `admin: true`.
The credential is an OAuth access token. Credential values were never retained.

## Exact external refusal

`PUT /user/installations/179966090/repositories/871087402` returned HTTP 403:

> You do not have permission to modify this app on Hexalith. Please contact an Organization Owner.

GitHub request ID: `CC88:23FD89:20FBBB5:31735F4:6AFB5729`.
The request used the maintainer profile through a command-local `GH_CONFIG_DIR`;
its existing `repo` and `admin:org` scopes and the account's owner role did not
make this credential acceptable for the operation. The current credential also
could not list installation repositories (HTTP 403); the complete selected set
is therefore unverified. No scope refresh or new credential was attempted.

`installations-before.stdout` and `installations-after.json` prove the App's
permission map and `selected` repository selection mode are unchanged. GitHub
rejected the singular addition; no successful access mutation is claimed.

## Required continuation

In [the existing CiCd App installation settings](https://github.com/organizations/Hexalith/settings/installations/179966090),
an owner session must add `Hexalith.Projects` under selected repositories and
save, preserving all existing selected repositories and App permissions.
The current CLI credential cannot perform that save through the attempted API.
No broader App permissions are required for the already qualified writer.

After that external grant, recheck live CiCd and Projects source against the
manifest and dispatch `deliver.yml` with `delivery=projects-g6-catalog` from
current CiCd main. Do not rerun the old stale owner source or push directly to
Projects. Retain the new qualification and delivery artifacts, and collect fresh
Projects CI/G-6 evidence bound to the actual delivered SHA. Local/hosted owner
qualification is already retained in the preceding packet; actual correction
delivery and corrected hosted acceptance remain pending. No module push or
Story 1.17 tracking change was made during this access attempt.

`result.json` records the bounded outcome; `grant-projects.stdout` and its
receipt retain the exact request and response. No disposable builds or tests
were needed for this administrative continuation.
