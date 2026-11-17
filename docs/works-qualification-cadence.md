# Works qualification cadence

The approved Works spec `spec-reduce-works-ci-duration.md` selects ordinary
push/PR product CI plus complete nightly/manual qualification. Its baseline is
`f88f99573114fb112a61163dbbd6c88f03df413c`. This is a finite local proposal for
unadopted Works, independent of the older package-metadata repair authorization.
It authorizes no commit, push, remote dispatch, publication or adoption.

`tools/repair_works_qualification_cadence.py` moves the complete existing
`platform-parity` job from `ci.yml` to `qualification.yml`, scheduled at 02:23 UTC
and available through manual dispatch. The job's steps, execution pins, artifact
retention, Release/package profile, eleven rows, 44 proof kinds, Agents refusal
and LocalScaffold probes, integrity closure and complete rollback remain intact.
All unrelated CI jobs and publication protection remain byte-for-byte preserved.
The release source-proof step requires successful ordinary push CI and complete
Qualification on the exact current `main` SHA before production environment
approval or publication credentials. Works implements that behavior in
`scripts/validate-release-source.sh`; a successful older nightly cannot qualify
a newer release commit. Dispatch Qualification manually on current `main` when
necessary, then wait for success before an authorized release.

The materializer accepts the approved baseline or its descendants only when the
owned input workflow blobs remain identical to that baseline. The concrete
proposal binds the exact current Works commit/tree, per-file Git blobs and
SHA256s, result tree and patch digest. It also binds the official CiCd owner's
current commit and exact materializer/helper SHA256s, allowing the approved
local implementation to be tested without committing it. Changed owner bytes,
source movement after preparation, tampering, adoption, foreign repository
origins, pre-existing qualification files, dirty/staged workflow inputs,
symlinks, hard-linked aliases and executable modes refuse before any target
write. Foreign files, index, refs and commits remain untouched. This local
receipt grants no release qualification or publication authority.

From the CiCd owner checkout:

```bash
run-with-temp python3 tools/repair_works_qualification_cadence.py prepare \
  --module /absolute/path/to/Works --proposal /absolute/path/to/new-proposal
run-with-temp python3 tools/repair_works_qualification_cadence.py apply \
  --module /absolute/path/to/Works --proposal /absolute/path/to/new-proposal
run-with-temp python3 -I tools/tests/test_repair_works_qualification_cadence.py -q
```

The local proposal and application receipt are retained under
`docs/proposals/works-qualification-cadence-20261117/`. The bound Works source is
`e70604d17dd4e7caccbe18e51024831f880b2ec4`, an unrelated recovery calibration
commit that arrived after the spec baseline; its workflow blobs match the
approved baseline exactly. The materializer preserved that external commit and
all foreign working changes. Offline release-source tests cover absent, stale,
failed and successful exact-source CI/qualification. Owner tests verify complete
job/pin and unrelated content preservation, source binding and write refusals.
Actionlint checks the materialized workflows. No module workflow-YAML assertion
tests were added.

Hosted run 44049423249 measured 44m12s for qualification and 8m13s for ordinary
compilation/tests before this change. Approximately eight minutes is the chosen
ordinary feedback target, not a new measurement. Platform's command ledger now
records UTC boundaries and monotonic elapsed seconds, including failed commands,
and refuses malformed persisted evidence prefixes immediately. Complete local
canonical qualification is reported separately. Hosted durations remain to be
measured after an authorized publication.
