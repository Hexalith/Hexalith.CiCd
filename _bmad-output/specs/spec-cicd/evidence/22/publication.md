# Story 22 publication scope

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

Consequently the product changes are published as a reviewable bundle in CiCd;
they are not pushed to Memories main past its outstanding verification gate.
No credential was broadened, guard bypassed, skip introduced, adoption enabled,
or legacy publishing credential revoked. Story 22 remains in progress.
