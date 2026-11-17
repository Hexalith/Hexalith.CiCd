# Draft McpCli CI budget — 2026-11-16

The Linux registration must request 360 minutes. The source now uses these
aggregate bounds, including process-tree termination and diagnostic headroom:

| Work | Bound |
| --- | ---: |
| Product hook non-live phase, including package staging | 3,600 s + 30 s kill grace = 60.5 min |
| Native preparation | 2,280 s + 30 s kill grace = 38.5 min |
| Complete native execution | 13,800 s + 30 s kill grace = 230.5 min |
| Shared guard, checkout, SDK/runtime setup, one solution build and ordinary units | reserved 20 min |
| Artifact upload and final runner/scratch cleanup | reserved 10.5 min |
| Total | 360 min |

This table bounds the shared Linux job only. Windows and macOS jobs depend on
that job and finish afterward, with their own platform preparation and command
bounds. The complete workflow wall clock therefore includes the Linux duration
plus the slower dependent platform lane; this table does not prove a 360-minute
workflow bound. Actual platform preparation, package/consumer/suite timings and
complete workflow duration remain required acceptance observations.

The three bounded script aggregates occupy 19,770 seconds (329.5 minutes).
The remaining 1,830 seconds (30.5 minutes) are reserved for shared work and
uploads/cleanup. Package staging is inside the first aggregate, rather than a
separate uncounted action. Its two 300-second no-build packs, 60-second version
query and 30-second built-tool query therefore cannot extend that aggregate.
Other child limits are subordinate bounds; hitting the aggregate fails the
job and cleans owned descendants rather than removing test cases.

The 22 approved companion-plan vectors, each existing 45-second plan deadline,
and each existing 960-second child deadline remain intact. The two independent
960-second child bounds also remain intact. Native execution reserves 600
seconds around the vector aggregate for cleanup/diagnostics, leaving the
vector aggregate 11,280 seconds after the two independent cases. This aggregate
intentionally does not promise every vector its maximum child duration in one
successful job. No case is dropped, skipped or accepted after a timeout.

Observed local timings are useful only for their actual scope: final product
script qualification took 17.829 seconds for 70 controlled tests; targeted
native launcher regressions took 247.074 seconds for 16 controlled cases.
These do not establish the complete live module runtime. The required Projects
contract is still unavailable publicly, preventing complete restored module,
consumer and live qualification. Shared hosted CI 43914543010 proved the real
native installer and three platform sample lanes on exact source
1f41d266bd4bd04acde7b64e8c907eb34233fe0f, but does not establish McpCli timing.

Acceptance still requires actual complete module timing, with measured shared,
non-live, preparation, live, upload and cleanup durations fitting the stated
reserves on the final committed product source. If those observations exceed
the budget, reduce redundant work or improve execution while preserving every
case, audits, isolation and failure behavior; do not claim this arithmetic
alone is empirical acceptance.

The final controlled launcher regression suite passed all 109 tests in
2,539.651 seconds (42.3275 minutes) on private Python 3.12.13/jsonschema 4.26.0
with unchanged before/after production source hashes. The host was heavily
loaded; this measures that local controlled suite only. It does not establish
the complete non-live phase, live lane, OS lanes or overall workflow timing.
