# Story 22 publication scope

The latest recorded publication is Memories main
`262232e498511b51b5d01e769725ecc299519238`, as work in progress. The later
explicit instruction recorded in the approved spec superseded the initial
publication hold described below. This did not satisfy the incomplete
pre-adoption verification procedure or authorize adoption. The authoritative
receipt is [workspace-publication.json](workspace-publication.json).

## Initial preflight and hold

On 2026-11-16 the human requested pushing all changes to main. This explicitly
authorizes remote publication after the earlier local-only implementation stage.
The CiCd publication contains the approved spec, implementation/evidence,
prerequisite handoff and complete portable Memories product-change bundle.
It does not register or adopt Memories, change a module gitlink, or publish
unrelated concurrent working-tree changes.

The complete local Memories candidate remains
`22723f99ed8a3f0abe306a4634836737be7f838d`, preserved by the bundle whose SHA-256
is recorded in `local-candidate.json`. Current remote Memories main was read
with module-agent authentication and remains
`c64e292a46858058f6764095c8e01c2faa0ff3e0` at the publication preflight.

The required command `python3 references/Hexalith.Builds/check.py` was repeated
in a disposable standalone clone with a genuine GitHub origin and its exact
committed Builds gitlink. It exits 1 because `.github/hexalith-ci.json` is absent.
The approved pre-adoption alternative remains incomplete: released shared
support, full applicable runtime/product and package-consumer qualification,
the unchanged telemetry approval/input conflict and AD-21 preconditions remain
outstanding. `publication-preflight.json` retains the exact refusal and intended
authentication metadata without credential material.

At that initial preflight, the product changes were held as a reviewable bundle
in CiCd rather than pushed to Memories main. That was the initial decision,
not the final publication state.

## Subsequent explicit publication

After disclosure of the refusal, the human repeated “push all changes” and “on
main”. Existing product preparation was reapplied by cherry-pick onto fresh
Memories main `5c1c22583fb4037997b266942a4fd4e05a245ebf` and published with
module-agent authentication at the revision above. GitHub reported bypassing
the PR requirement and three required status checks. Qualification stayed
incomplete; the checker still refused the missing adoption configuration.

The resumed local assessment proves that all 253 changed paths at that recorded
published revision have the same bytes, modes and gitlinks as the preserved
local candidate, and that the 17 owned/output groups are unchanged from each
respective base. This is a local-object comparison, not new compilation or
remote-state authentication. See [resumed-local-verification.json](resumed-local-verification.json).

Registration, adoption, immediate scoped credential cleanup, green adopted CI
and the next scheduled nightly outcome remain gated. No additional remote
operation was performed during the resumed local implementation stage.
Story 22 remains in progress; [resumed-implementation.md](resumed-implementation.md)
records the remaining implementation gates.
