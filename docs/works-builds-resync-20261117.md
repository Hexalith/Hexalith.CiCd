# Works Builds synchronization after the catalog refresh

This [bounded owner proposal](proposals/works-builds-resync-20261117.json)
authorizes exactly `references/Hexalith.Builds`, mode `160000`, in Works. Against
Works base `e89d8b8b7ffc33d9ef7f53e4ee420bae9e7fc469`, replace
`07fdb22578ba55e092b2db1b4ff43f253b53fbbf` with published commit
`af3752ddcbe94c007630703ab3803df5654f9933`. The user's explicit repository and
submodule synchronization request supplies application authority; this owner
record satisfies the shared instruction to propose owned changes in CiCd.

The target preserves both local and upstream histories and has exactly the tree
of the reviewed upstream commit `a1e0c310b1f1a50d78e6132890fae6bcba769f6d`.
Official GitHub commit and comparison APIs establish that the target is published
and reachable from the observed `main`. The target is frozen; later upstream
advances are outside this proposal.

The only catalog-property change from the previous Works input is
`HexalithOpenApiVersion`, selecting `Microsoft.OpenApi` 3.11.1 instead of 3.11.0.
The associated audit refresh changes that package entry and its one family
decision, preserves the other 316 package entries and 156 family decisions, and
retains the consumer inventory except its repository-revision provenance.
The audit's raw catalog hash matches the selected catalog bytes. Every other
file under `Props/` is byte-identical. This supersedes the earlier proposal's
unchanged-catalog observation for this new target; it preserves that historical
observation for its original revisions.

The synchronization's seven focused checks passed: 362 catalog probes, the
317-package/157-family audit, seven Tools environment modes, ten guard-tool
cases, twenty action cases, CI-environment controls, and local-check controls.
These focused observations do not establish green exact-source hosted CI or
release acceptance. The proposal records the actual hosted run state without
claiming a pass. The previous `07fdb225` CI success does not qualify this target.
Fresh Works Debug/source compilation, required CI, canonical Platform parity,
release and publication checks remain required against the selected inputs.

A private disposable Git index and object store proved that the result tree
changes only this one gitlink. The root `.gitmodules` identity, .NET SDK 11.0.100
selection and existing workflows remain unchanged. The pending product files,
Platform checkout and shared root index were fingerprinted and preserved.
No physical Builds checkout, root source file or root index was written here.
The parent stages this exact delta with its separately authorized product and
Platform updates after this owner record is committed and pushed. No controller,
adoption, workflow change, publication or approval waiver is introduced.
