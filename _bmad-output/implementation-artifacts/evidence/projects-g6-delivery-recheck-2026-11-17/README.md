# Projects G-6 correction: delivered; acquisition verified; package gates remain red

This recheck found the requested narrow implementation and owner delivery already
completed after the original handoff. It verifies that outcome and current
source; it makes no new production change or delivery attempt. The closed
proposal remains bound to its reviewed base/result and must not be reapplied to
the later product source. Story 1.17 tracking is unchanged.

[CiCd owner run 43939511545](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/43939511545)
qualified source `2a1128e0106baed22999c4687d7d15e7639f22cf` and delivered Projects
`146d0f7e9964c82da23d31b51e6ab62efdcfdda6` through its existing scoped App.
Fresh GitHub artifact metadata authenticates the retained qualification and
delivery ZIPs by SHA256. Their extracted receipts are retained here.
[Independent source proof](source-proof.json) checks the sole reviewed parent,
complete result tree, exactly three changed paths and unchanged other entries,
pins and gitlinks. The same action and invocation blobs remain present at current
Projects `3361f2e3b5655fa1ad50a2d12c640bbd5edcbb4b`, before Conversations
prepare-build. No proposal refresh is required. The mapper remains unchanged.

All **62 behavioral tests passed** in a disposable exact-owner-source checkout:
17 acquisition, 28 controller and 17 workflow cases, using locked Python 3.12
scripts and the exact existing Builds v5.1.0 fixture. Invocation:
`run-with-temp python3 -B recheck.py`. The private directory was removed after
all children completed. [Local qualification](local-qualification.json) binds
source `4db3776e444f0ec6e5f97d1ff089a0d83f990082` and log hashes. The subsequent
observed owner main has identical relevant blobs; its comparison is retained.
This is behavioral qualification, distinct from the earlier actual delivery.

[Completed Projects CI 43967083172](https://github.com/Hexalith/Hexalith.Projects/actions/runs/43967083172)
is bound to `cdacfb2a2c9d1eb23f2dbd59b53f42b945e80f37`. Its newly downloaded,
digest-verified artifact reports `prepared`, `acquired: true`, exact catalog
`e2bbbd0893f586e4d447ef8358ff747ea3d34435`, SHA256
`d098dab50977041a536508f6df7e934f95678a4a0abedd80b28e9bae19ee0637`, and preserved
source HEADs, indices, refs and gitlinks. Conversations also reports `prepared`.
The catalog acquisition correction therefore has actual hosted evidence.

Full CI/G-6 runtime acceptance remains blocked by subsequent package failures:

- G-6's unchanged effective-graph `dotnet restore` of McpCli fails with NU1102:
  `Hexalith.Projects.Contracts >= 2.0.0-story66.3` is unavailable from nuget.org;
  the nearest listed version is 1.2.4. The prerequisite is the required artifact
  on an approved feed or an explicit owner-approved dependency alignment.
- [Current-source CI 43982007709](https://github.com/Hexalith/Hexalith.Projects/actions/runs/43982007709)
  has already failed its Release build with CS0234 because
  `QueryResultContractAttribute`/`QueryResultContract` is absent from the pinned
  EventStore 5.1.1 API. Compatible package/API artifacts or an owner-approved
  alignment are required. G-6 remained queued at the last retained observation;
  no current-source runtime pass is claimed.

[Final result](final-result.json) records exact commands, source identities,
job IDs and missing prerequisites. Full masked logs, job observations, original
owner receipts, the authenticated hosted ZIP and extracted acquisition/mapper
receipts are retained here. [Preservation observations](preservation-recheck.json)
distinguish concurrent commits/index/evidence changes from this recheck, whose
writes are confined to this new directory. Tracking hashes remain unchanged.
No credential, pin, workflow, gate, nested submodule, publication/audit/A8,
deployment or v2-activation change was made by this recheck.
