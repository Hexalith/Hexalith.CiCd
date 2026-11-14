# Nightly bump transport qualification

Status: **incomplete — hosted job-token evidence required**.

The default implementation uses the `bump-push` job's `GITHUB_TOKEN` with
Contents and Actions write, verifies the exact candidate, pushes it by ordinary
fast-forward, and explicitly dispatches `deliver.yml` on main after confirmed
push. Fixture tests verify the data and controller boundaries. They do not prove
whether GitHub accepts a push changing a nested
`rendered/<Repo>/.github/workflows/*.yml` path.

Dispatch `nightly.yml` on `main` with **qualify-bump: true** to exercise that exact
job token on an isolated temporary probe ref. All release, production bump,
delivery observation and keepalive jobs are skipped in this mode. The probe's
child commit changes only the inert
`rendered/Hexalith.Probe/.github/workflows/probe.yml` file. It must neither push
main nor dispatch any release/delivery nor touch module repositories. Record
its actual remote SHA/tree and the controller's cleanup evidence from the
`hexalith-nightly-bump-push-<attempt>` artifact before accepting a result.

A successful push qualifies the job-token route; delivery dispatch/trigger
behavior must also be validated with fixture modules before story acceptance.
A definite GitHub rejection specifically for Workflows permission on that nested
path selects the architecture's App fallback: put `bump-push` in `cicd-app`, mint
a fresh CiCd-only Contents/Workflows write token through the pinned action, keep
the same independent verifier, set `BUMP_TRANSPORT=app`, and omit explicit delivery
dispatch because its push trigger starts delivery. An unrelated 401/403,
transport failure or uncertain write leaves qualification incomplete and is
never evidence of either route's success or of a Workflows rejection.

For that fallback, pass the App token as `CICD_TOKEN` and that same job's
Actions-read `GITHUB_TOKEN` as `HANDOFF_TOKEN` for artifact authentication. This
keeps the App mint limited to Contents and Workflows write on CiCd.

## Evidence to complete

| Evidence | Value |
| --- | --- |
| Controller/workflow source revision (full SHA) | Pending |
| Hosted probe run URL and attempt | Pending |
| Probe base, child and actual remote commit/tree (full SHAs) | Pending |
| Job-token outcome or exact definite Workflows rejection | Pending |
| Probe ref/workflow cleanup evidence | Pending |
| Selected production transport | Default job-token route; not yet hosted-qualified |
| Fixture-only delivery run and qualifying module CI links | Pending |
| Final delivery trigger/dispatch confirmation and cleanup | Pending |

No hosted qualification or production adoption has been claimed by this file.
