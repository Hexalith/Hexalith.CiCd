# Story 26 local prerequisite assessment — 2026-11-16

**Verdict: blocked on the separately scoped released prerequisite.** No Platform
preparation, registration or adoption was performed. The implementation step
permits local work only; no remote read, administration, push, delivery or
publication was attempted.

The spec and its complete frontmatter context (`investigation.md`) were read
before this assessment. [The local record](local-readiness.json) contains exact
identities, tagged contract hashes, captured check output and before/after
Platform preservation evidence.

## Release boundary

- CiCd remains at `f95d46357e5378f2ed8a3da186fb4a543dc7b7ff`, with the
  pre-existing dirty workspace preserved.
- `builds-version` selects `v6.0.6`, peeled locally to
  `fdda17c0a4538b0f7c99f813c20ca24b49006530`.
- At that exact tag, `schemas/hexalith.ci.v1.json` has no producer-preparation
  input; `Github/lib/module_preparation.py` is absent. The inspected
  `restore_and_build` implementation invokes restore and build directly.
  It cannot provide Platform's authenticated Tooling/EventStoreHost assemblies
  before evaluation through the required shared preparation path.
- The local Builds checkout is newer source,
  `05bda4e01d70afacb5048d5c336f383a301c0974`, and contains managed preparation.
  No locally available tag contains that revision; the newest local stable tag
  remains `v6.0.6`. This is source evidence, not an acceptable released contract
  or proof of the separately required Platform qualification.
- Local tags do not establish the newest remotely available release. Remote
  availability and administrative state were not reverified in this local-only
  step. The earlier `preflight.json` remains historical evidence.

Platform remains at `c2236a9f95c37d4d2ef8dee3fe2cbfe5e9ab41d2` in both its
checkout and parent gitlink. Its producer remains historical Builds `v6.0.5`,
`e2bbbd0893f586e4d447ef8358ff747ea3d34435`; it was not relabeled as the active
catalog. The SDK, package-mode/reference refusals, cohort scripts, package
assertions and real security remediations remain unchanged.

## Checks and preservation

- `run-with-temp uv run --locked --script tools/render.py --check` passed
  (exit 0), with `UV_OFFLINE=true` and Python downloads disabled. This validates
  the current renderer output; it does not establish Platform readiness.
- From the Platform root,
  `run-with-temp python3 references/Hexalith.Builds/check.py` exited 2 because
  the nested checker is absent. This is an unsuccessful check. No nested
  submodule was initialized and no prospective owned state was overlaid.
- Before/after snapshots agree for all 29,700 tracked Platform entries,
  including worktree bytes, filesystem modes, index entries and direct
  gitlinks. The module remained clean; all 17 nested gitlinks remained
  uninitialized. Parent HEAD/index Platform gitlinks also agree.
- Product package-mode qualification was not run: the spec requires a verified
  acceptable shared release before dependent preparation. No exact preparation
  candidate was created, so the pre-adoption push exception has no passing
  result to consume.
- `tools/validate.py` was not run. There is no registered committed Platform
  candidate, and the validator clones remote repositories. Global and Platform
  committed-candidate verdicts remain outstanding.

## Outstanding execution

All seven execution tasks remain unchecked. AD-21 provisioning and authenticated
before/after settings, NuGet policy/Zot ACL/App selection, exact product
preparation and cohort/package checks, registration and committed render,
App delivery/preservation, cleanup, adopted CI and the next scheduled nightly
remain outstanding. No migration acceptance criterion is claimed.

The next dependency is
[`prerequisite-26-platform-build-preparation.md`](../../../../implementation-artifacts/prerequisite-26-platform-build-preparation.md):
implement and qualify its demonstrated shared gaps separately, publish through
the authorized shared process, and record an acceptable exact tag/source with
Platform preparation, compatibility and package qualification. Story 26 then
consumes that release. Newer untagged source or a hook that restores/builds is
not a substitute for this dependency.
