# Works Builds gitlink synchronization

This bounded owner proposal covers exactly `references/Hexalith.Builds`, mode
`160000`, in Hexalith.Works. The user explicitly authorized synchronizing and
pushing the repository/submodules and fixing CI blockers without another human
checkpoint. The [recorded proposal](proposals/works-builds-gitlink-20261117.json)
satisfies the shared instruction to propose owned CI/CD changes in CiCd.

Against Works base `275896654181276eda49b9c927de876ca5a659ae`, replace the
gitlink `cbd13a1e93015182439112918cae4216b953f9bf` with verified published commit
`07fdb22578ba55e092b2db1b4ff43f253b53fbbf`. The target includes the strict
explicit-catalog-default reader correction and its historical test-fixture
repair. Its focused Debug build passed with zero warnings/errors and auditing
enabled; 24 direct-catalog and six default-selection/refusal cases passed with
no skips. These observations do not establish a green hosted CI result.

Builds' official `main` was observed at
`2ee32885ae96805c7745c519275e351ebb229720`; the selected `07fdb225` target is
its verified ancestor. The later upstream commit is a future input and is not
imported by this proposal. Exact-source
[CI43973769780](https://github.com/Hexalith/Hexalith.Builds/actions/runs/43973769780)
was still running when the proposal was prepared; its recorded state is an
observation, never release acceptance or a waiver.

The package catalog and package-version audit have identical Git blobs and
SHA256s at the before/after revisions. The root `.gitmodules` body, declared
Builds path and official URL remain unchanged. A private disposable Git index
verified that the proposed tree changes precisely this one gitlink. The five
pending workflow results still match the separately committed metadata-auth
owner proposal exactly; no additional workflow or other owned mutation is
introduced here.

The parent applies this same gitlink delta in its final combined Works commit,
preserving separately authorized product changes and other submodule updates.
The proposal's result tree describes the single-path delta against the stated
base, not that combined product commit. No root source/index write, adoption,
controller, workflow change, dependency update or publication occurs in this
owner record. Normal exact-source CI and publication verification remain due.
