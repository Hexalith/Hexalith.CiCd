# Preparation qualification tools

These runners retain the existing module-specific preparation approvals and
historical source requirements described in
[pre-adoption publication](../../docs/pre-adoption-publication.md). Relocation
does not qualify a new module candidate or expand publication authority.
Inspect their pinned historical inputs before reuse and run disposable jobs
with `run-with-temp`.

| Entry point | Frozen inputs | Raw output |
| --- | --- | --- |
| `qualify-owning-g6.py`, `run(root, scratch)` | `fixtures/deterministic-support.json`: the 21 retained `Hexalith.EventStore.Server.Tests` method selectors projected from Projects' historical attempt-16 G-6 capture; the Projects checkout under qualification no longer supplies them | Supplied `scratch` directory |
| `pre-adoption/folders/verify-product-candidate.py` | Sibling `fixtures/` registration configuration and projected attempts 1/2 | `$TMPDIR/folders-product-results/` |
| `pre-adoption/folders/verify-final-candidate.py` | Sibling `fixtures/` registration configuration and projected attempt 3 | `$TMPDIR/folders-final-results/` |
| `pre-adoption/projects/local-package-build.py` | Direct source checkouts; G-6 resolves from this CiCd tools tree | `$TMPDIR`, stdout |
| `pre-adoption/eventstore/pre-adoption-verify.py` | Sibling `fixtures/planned-configuration.json` | Explicit required `--report` outside the verifier's `$TMPDIR`; remaining work beneath it |
| `pre-adoption/parties/qualify-push.py` | Sibling `fixtures/` state, accepted receipt, complete patch, normalization and projected dependency receipt | `$TMPDIR/parties-publication-results/` |

The story 28-3 relocation record identifies the original and relocated runner
and fixture blobs. Whole-copy
proof inputs retain their bytes. Receipt projections contain only the approved
consumed fields, and original receipts remain in history and their existing
locations. Fixture identities are checked by
`tools/tests/test_qualification_fixtures.py`.
The whole Parties patch includes inert deleted-source path strings and has an
exact-identity provenance exception; no fixture-directory exemption exists.
Reused Folders product commands keep the `log` value of their source receipt
(`attempt-1/…`, `attempt-2/…`). Those names are relative to story 17's original
evidence directory, where the historical logs remain; they do not resolve beside
the new scratch output. `conversations_fixture_results.py` is a separate
product-fixture result qualifier, not one of the relocated preparation runners.

`run-with-temp` removes `$TMPDIR`, including the default outputs above, when its
command exits. Copy what a receipt needs before the wrapper returns, for example
`run-with-temp sh -c 'python3 RUNNER; status=$?; cp -R "$TMPDIR/folders-product-results" /absolute/durable/path; exit $status'`,
then record digests and one-line results instead of committing raw output.
Parties also prints its complete record, including both commit messages, to
stdout.

Run the reusable relocation exercise from a clean CiCd checkout:

```sh
run-with-temp python3 tools/qualification/exercise_relocation.py
```

The exercise executes the relocated runner bodies and frozen fixture reads with
disposable module sources and controlled external Git, SDK, container, network
and released-policy boundaries. It checks scratch outputs and retained failures,
including Parties' refusal of an intentionally mismatched source body after all
proof fixtures and dependency pins are read. A separate synthetic Parties
success case checks both commit messages beneath scratch. Its result proves relocation and
preserved control flow; actual product readiness, released-policy acceptance and
publication still require the approved procedures on exact real inputs.
