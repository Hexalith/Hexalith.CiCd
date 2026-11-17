# Story 14 Agents preparation push, 2026-11-17

The human asked to publish the Agents product files and rerun the full
floors. This is not adoption, registration, credential cleanup or a
nightly outcome.

## Candidate

Product files only, reapplied onto freshly fetched `origin/main`:

- `eng/consumer-executable-assets.json`
- `test/Hexalith.Agents.Server.Tests/BuildContractConformanceTests.cs`

Owned workflows, dependabot, instruction blocks, deny entries and the
Builds gitlink were not edited.

The first qualified commit `d4b4e8937cf00e05057a5455a08bbaba79a8f4af`
was based on `e98dab8c243286ceb8d0db8998caf3aad7f7b089`. Immediate
pre-push fetch showed remote main had moved to
`9ba1c5c1b3e17676c70be058d1a7cd8b7539dea1` (`fix: submodule`, adding
`references/Hexalith.CiCd`). The fast-forward was refused. That write
stopped. The two product files were reapplied onto the new main as
`2d7a4cf96d67ba27458c49fdbaca9ff23d1c0c9a` and the approved proof was
run again. See [`concurrent-main.json`](concurrent-main.json).

## Approved preparation proof

[`qualification.json`](qualification.json) binds disposable clones of
the reapplied candidate. Released policy is immutable Builds `v6.2.0`
(`0ccd12af6576a3aac601340dec7dba53e86768c3`); see
[`released-policy-proof.json`](released-policy-proof.json).

- Ordinary `check.py` refused missing `.github/hexalith-ci.json`.
- Released audit lint and pinned commitlint (shared v6.2.0 and owning
  Agents policy) passed for the exact message.
- Package-mode Release restore/build succeeded.
- Ordered floors with fail-skips, zero failures, zero skips:
  Contracts 2005 (529), Client 7 (6), Domain 1084 (787), Server 2063
  (549), UI 1362 (1073). Total 6521.
- Real hook: six packages, seven consumers, scratch removed.
- Exact exclusion regressions passed. Owned perimeter matched the
  fresh base.

The first checker invocation on a local-path origin is retained as
[`agents-normal-checker-local-origin.log`](agents-normal-checker-local-origin.log).
The superseded `e98dab8` qualification is
[`qualification-d4b4e89-superseded-by-concurrent-main.json`](qualification-d4b4e89-superseded-by-concurrent-main.json).

## Publication

Module-agent fast-forwarded `9ba1c5c..2d7a4cf` to `main`. Authenticated
readback is `2d7a4cf96d67ba27458c49fdbaca9ff23d1c0c9a`. No force push
and no credential fallback. See
[`Hexalith.Agents-push.json`](Hexalith.Agents-push.json).

Story 11's genuine scheduled night, Conversations discovery errors,
AD-21 refresh, registration, App delivery and the next nightly remain
open. Resume those after the owning stories land.
