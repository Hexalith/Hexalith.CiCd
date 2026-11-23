# Story 23 read-only preflight preparation

The next preflight is prepared locally. No GitHub requests, provisioning,
product changes, release, pin update or delivery ran during this preparation.
Historical `preflight.json` and `maintainer-preflight.json` remain unchanged.

The [preflight tool](../../../../../tools/qualification/pre-adoption/tenants/read-preflight.py)
now follows GitHub pagination for every collection it reads,
including ruleset details and the release environment discovered on later pages.
It includes release-environment branch policies and inventories every observed
selected organization grant, alongside known prerequisites. The paired legacy
secret is `HEXALITH_ZOT_API_KEY`.

Each page retains its HTTP status, exit code, permission/scope headers, pagination
metadata and API error. Refused, inaccessible, malformed and transport-failed
reads cannot become empty successful inventories. Later failures preserve prior
items and mark the collection incomplete. Changed counts, repeated identities,
missing pages and links that change the collection/filter also remain unverified.
The packet records readbacks, not satisfaction of AD-21 or product verification.

Imports perform no work. The CLI requires an explicit existing credential
profile and a new output destination; it rejects inherited token overrides and
never overwrites historical evidence. Debug tracing is removed from subprocess
environments, and module-token responses are redacted. The helper does not run
the product checker as part of a configuration inventory.

## Verification

The current suite runs with `run-with-temp`. The offline tests forbid all
subprocess execution, including at import time.

```text
run-with-temp python3.12 -B tools/tests/test_tenants_read_preflight.py -v
```

The earlier eleven-test run passed on Python 3.12 and 3.14. The retained logs are
`preflight-offline-python312.log` and
`preflight-offline-python314.log`. Coverage includes complete two-page inventory
execution, later-page discovery and refusal, malformed/timeout responses,
untrusted pagination, incomplete or changing counts, duplicate records,
credential redaction and CLI preservation of existing evidence/profile settings.
`git diff --check` passed for the reader changes.

The first authorized refresh exposed GitHub's numeric CodeQL pagination route.
The reader now accepts `/repositories/1174267565/code-scanning/analyses` only
after a successful metadata read confirms both that integer repository ID and
`Hexalith/Hexalith.Tenants`. Other repository IDs, endpoint suffixes, hosts,
filters and nonconsecutive pages remain refused. The expanded 14-test suite
passed offline on Python 3.12 and 3.14; logs are
`preflight-alias-offline-python312.log` and
`preflight-alias-offline-python314.log`. This correction made no remote requests.
The first incomplete packet, `maintainer-preflight-authorized-resume.json`,
remains unchanged with SHA-256
`5d828e1d7242afd6397a9a409b1670ecdb08bafdb9bbd94de5d70a840180a0e5`.

## Operator handoff

During a later authorized remote phase, refresh through the existing maintainer
profile without changing the default profile. The output path below must be new:

```bash
GH_CONFIG_DIR=/home/administrator/.config/gh python3 -B tools/qualification/pre-adoption/tenants/read-preflight.py --output /absolute/path/to/maintainer-preflight-next.json
```

Exit 2 retains the packet and reports failed requests or incomplete collections.
A 404 remains `not-found-or-inaccessible`; it is not an absence certification.
The existing App-selection refusal still needs installation settings access or
an appropriate App-authorized read. No App key is needed for local preparation.
Inspect the fresh packet before executing the ordered AD-21 provisioning steps;
retain existing publication policies until actual adoption. The compatible
Builds release/pin, Tenants product work, registration, adoption cleanup, green
adopted CI and next scheduled nightly outcome remain incomplete.

The dated qualification driver and provisioning capture belong to the
historical packet at `97538b46caec91945d25b496ff1135bab475f2b0`. That
revision retains their adjacent inputs at the original paths.
