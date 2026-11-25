---
title: 'Migrate Agents'
type: 'chore'
created: '2026-11-25'
status: done
baseline_revision: d04c9ab7a8fa43dc6dac1f15d34135aba8e79551
---

# Story 14. Migrate Agents

Story 14 was built and accepted through bmad-build before the story backlog
tracked it in this folder. The [Agents migration spec](../../../implementation-artifacts/spec-14-migrate-agents.md)
is the record of intent, tasks, acceptance criteria, review triage and
verification. This file records that completion so the story is not dispatched
again from [stories.yaml](../stories.yaml).

- Spec blob `d2aebdee8ee1b7b226a1b1566ee61155426612fb`, status `done`, last
  changed by `1cd147cc509adbdd3187f4e1d89fb3b128627b79` (tree
  `158840a61cd14ec49651081e0896000b4342fc19`), which closed review finding BH7
  through the trusted publishing decision of 22 November 2026.
- Completion commit `b7102103ebbe2d3644f9c080834306d890ccbc3d` (tree
  `7b52764a6c90535f3dbd69c7c3c75198dbc3a202`), 21 November 2026, after review
  loop 1 was applied in `09297e0e21fdf62c293ebac7507f7ff4bf40ad4f` and verified
  in `d85c70c13321d54beab7871253e1f0e781110420`.
- Registration `8e43d8c59b3cc8f2798b2ba8ce90161fc653128f`. Delivery run
  [44886812692](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/44886812692)
  adopted Agents with a byte-identical perimeter.
- Nightly acceptance: `tools/nightly_acceptance.py` judged Agents `pass` on
  on-demand Nightly [44890586692](https://github.com/Hexalith/Hexalith.CiCd/actions/runs/44890586692).
  Release run 44890634855 published immutable `v2.0.3`.
- [Adoption evidence](../evidence/14/adoption-20261121/README.md)
