# Works product restore fix — 2026-11-19

Adopted Works `main` `3996de28eecf32972e8469cbcd7426eaa56f24ab` failed hosted
CI [44621765615](https://github.com/Hexalith/Hexalith.Works/actions/runs/44621765615)
at Stage 2: NU1109 downgraded `Hexalith.EventStore.ServiceDefaults` from 5.3.1
to the Works pin 5.2.0 because Builds `v6.4.2` selects Tenants 8.0.2.

Architecture tests allow only the EventStore wrapper pin, so Tenants cannot be
overlaid in Works `Directory.Packages.props`. The product pin moved to EventStore
5.3.1 (catalog default on the adopted Builds tag). Source-identity files still
named EventStore `05e4f6d…` / PolymorphicSerializations `f1e2b45…` while the
committed gitlinks are `8bfc4ca…` / `df1a0e5…`; those were rebound to the
gitlinks. Owned workflows, `hexalith-ci.json`, Dependabot, and the Builds
gitlink were not edited.

## Candidate

- Branch `fix/eventstore-catalog-alignment`
- `7a8233af1645a7d0d77d617f5e0f310b4c2613d8` pin
- `d3a11121cbdee345d5f12151e5a2b91338aaae62` source-identity rebind
- PR https://github.com/Hexalith/Hexalith.Works/pull/18
- Pushed with `GH_CONFIG_DIR=$HOME/.config/gh-module-agent`

## Verification

- Isolated `run-with-temp` clone, GitHub origin, Builds+Platform+Parties at
  committed pins, `python3 references/Hexalith.Builds/check.py` exit 0
  (`checkpy-product-20261119-isolated.json`): Architecture 385, Property 3,
  Unit 597. Guard policy passed. Restore had 0 errors.
- Two in-tree `check.py` attempts hit MSB3026 on `Hexalith.Builds.Tooling.dll`
  (file lock / parallel copy); same flake as the preparation proof. Isolated
  clone with a private `TMPDIR` did not reproduce it.
- `scripts/verify-source-debug.py --check-only` status `passed`
  (`source-identity-product-20261119.json`).
- `check.py` does not run stage 4, the source-identity hook, or R1–R11.

## Still open on this story

- Merge PR 18 onto Works `main`.
- Hosted CI green on adopted main (stages 1–4, source-identity, 180-minute
  platform-parity).
- Maintainer nuget.org/org-secret/Zot/NUGET_API_KEY cleanup.
- Authenticated nightly CAP-13 after green main.
